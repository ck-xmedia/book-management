pipeline {
  agent any

  options {
    timestamps()
    ansiColor('xterm')
    timeout(time: 60, unit: 'MINUTES')
  }

  environment {
    APP_PORT = '8080'
    VENV_DIR = "${WORKSPACE}/.venv"
    PATH = "${VENV_DIR}/bin:${PATH}"
    PROJECT_TYPE = ''
  }

  stages {
    stage('Checkout') {
      steps {
        git branch: 'main', url: 'https://github.com/ck-xmedia/book-management.git'
      }
    }

    stage('Environment Setup') {
      steps {
        script {
          sh '''
            set -Eeuo pipefail

            mkdir -p logs

            # Prepare Python virtualenv if Python is available
            if command -v python3 >/dev/null 2>&1; then
              if [ ! -d "$VENV_DIR" ]; then
                python3 -m venv "$VENV_DIR" || true
              fi
              . "$VENV_DIR/bin/activate" || true
              python3 --version || true
              python3 -m pip --version || true
            fi

            # Detect project type by common build/dependency files
            detect_type() {
              if [ -f "pom.xml" ]; then echo maven; return; fi
              if [ -f "build.gradle" ] || [ -f "gradlew" ]; then echo gradle; return; fi
              if [ -f "package.json" ]; then echo node; return; fi
              if [ -f "requirements.txt" ] || [ -f "pyproject.toml" ]; then echo python; return; fi
              if ls *.csproj >/dev/null 2>&1; then echo dotnet; return; fi
              if [ -f "go.mod" ]; then echo go; return; fi
              if [ -f "Cargo.toml" ]; then echo rust; return; fi
              if [ -f "composer.json" ]; then echo php; return; fi
              echo unknown
            }

            TYPE="$(detect_type)"
            echo "$TYPE" > .project_type
            echo "Detected project type: $TYPE"
          '''
          env.PROJECT_TYPE = sh(returnStdout: true, script: "cat .project_type").trim()
          echo "PROJECT_TYPE=${env.PROJECT_TYPE}"
        }
      }
    }

    stage('Install Dependencies') {
      steps {
        script {
          def pt = env.PROJECT_TYPE ?: 'unknown'
          if (pt == 'node') {
            sh '''
              set -Eeuo pipefail
              node -v || true
              npm -v || true
              if [ -f package-lock.json ]; then
                npm ci
              else
                npm install --no-audit --no-fund
              fi
              # Build if a build script exists
              if grep -E '"build"\\s*:' package.json >/dev/null 2>&1; then
                npm run build || true
              fi
              test -d node_modules
            '''
          } else if (pt == 'python') {
            sh '''
              set -Eeuo pipefail
              if command -v python3 >/dev/null 2>&1; then
                python3 -m pip install --upgrade pip setuptools wheel || true
                if [ -f requirements.txt ]; then
                  python3 -m pip install -r requirements.txt
                fi
                if [ -f pyproject.toml ]; then
                  # Try PEP 517 build/install if applicable
                  python3 -m pip install .
                fi
                python3 -m pip freeze > logs/pip_freeze.txt || true
              fi
            '''
          } else if (pt == 'maven') {
            sh '''
              set -Eeuo pipefail
              mvn -v || true
              mvn -B -DskipTests clean package
              ls -l target || true
            '''
          } else if (pt == 'gradle') {
            sh '''
              set -Eeuo pipefail
              if [ -f gradlew ]; then
                chmod +x gradlew || true
                ./gradlew --version || true
                ./gradlew bootJar || ./gradlew assemble
              else
                gradle --version || true
                gradle assemble
              fi
              ls -l build/libs || true
            '''
          } else if (pt == 'dotnet') {
            sh '''
              set -Eeuo pipefail
              dotnet --info
              dotnet restore
              dotnet build -c Release
            '''
          } else if (pt == 'go') {
            sh '''
              set -Eeuo pipefail
              go version
              go mod download
              mkdir -p bin
              go build -o bin/app .
              test -x bin/app
            '''
          } else if (pt == 'rust') {
            sh '''
              set -Eeuo pipefail
              rustc --version || true
              cargo --version || true
              cargo build --release
              ls -l target/release || true
            '''
          } else if (pt == 'php') {
            sh '''
              set -Eeuo pipefail
              php -v || true
              if [ -f composer.json ]; then
                if command -v composer >/dev/null 2>&1; then
                  composer install --no-interaction --prefer-dist
                else
                  echo "Composer not found; skipping composer install." >&2
                fi
              fi
            '''
          } else {
            echo "Unknown project type; no dependencies to install."
          }
        }
      }
    }

    stage('Deploy Application') {
      steps {
        script {
          sh '''
            set -Eeuo pipefail
            trap 'status=$?; if [ "$status" -ne 0 ]; then echo "[ERROR] Deployment failed" | tee -a logs/deploy.log; fi' EXIT

            APP_PORT="${APP_PORT:-8080}"
            mkdir -p logs

            echo "[INFO] Terminating any process bound to port ${APP_PORT}" | tee -a logs/deploy.log
            if command -v lsof >/dev/null 2>&1; then
              PIDS="$(lsof -t -i :${APP_PORT} || true)"
              if [ -n "$PIDS" ]; then
                echo "$PIDS" | xargs -r kill -9 || true
              fi
            elif command -v fuser >/dev/null 2>&1; then
              fuser -k ${APP_PORT}/tcp || true
            else
              echo "[WARN] lsof/fuser not available; cannot pre-kill by port." | tee -a logs/deploy.log
            fi

            sleep 1
            rm -f app.pid || true

            TYPE="$(cat .project_type 2>/dev/null || echo unknown)"
            start_cmd=""

            case "$TYPE" in
              node)
                if [ -f package.json ] && grep -E '"start"\\s*:' package.json >/dev/null 2>&1; then
                  start_cmd="npm run start"
                elif [ -f server.js ]; then
                  start_cmd="node server.js"
                elif [ -f app.js ]; then
                  start_cmd="node app.js"
                elif [ -f index.js ]; then
                  start_cmd="node index.js"
                else
                  echo "[ERROR] Node project but no start script or entry file found." | tee -a logs/deploy.log
                  exit 1
                fi
                ;;
              python)
                if [ -f app.py ]; then
                  start_cmd="python app.py"
                elif [ -f main.py ]; then
                  start_cmd="python main.py"
                elif python -c "import flask" >/dev/null 2>&1; then
                  export FLASK_APP="${FLASK_APP:-app.py}"
                  start_cmd="flask run --host 0.0.0.0 --port ${APP_PORT}"
                else
                  start_cmd="python -m http.server ${APP_PORT}"
                fi
                ;;
              maven)
                JAR="$(ls target/*.jar 2>/dev/null | head -n 1 || true)"
                if [ -n "$JAR" ]; then
                  start_cmd="java -Dserver.port=${APP_PORT} -jar \"$JAR\""
                else
                  echo "[ERROR] Maven build artifact not found in target/." | tee -a logs/deploy.log
                  exit 1
                fi
                ;;
              gradle)
                JAR="$(ls build/libs/*.jar 2>/dev/null | head -n 1 || true)"
                if [ -n "$JAR" ]; then
                  start_cmd="java -Dserver.port=${APP_PORT} -jar \"$JAR\""
                else
                  echo "[ERROR] Gradle build artifact not found in build/libs/." | tee -a logs/deploy.log
                  exit 1
                fi
                ;;
              dotnet)
                start_cmd="dotnet run -c Release --urls http://0.0.0.0:${APP_PORT}"
                ;;
              go)
                if [ -x bin/app ]; then
                  start_cmd="PORT=${APP_PORT} ./bin/app"
                else
                  echo "[ERROR] Go binary bin/app not found." | tee -a logs/deploy.log
                  exit 1
                fi
                ;;
              rust)
                EXE="$(find target/release -maxdepth 1 -type f -perm -111 2>/dev/null | head -n 1 || true)"
                if [ -n "$EXE" ]; then
                  start_cmd="PORT=${APP_PORT} \"$EXE\""
                else
                  echo "[ERROR] Rust release binary not found in target/release/." | tee -a logs/deploy.log
                  exit 1
                fi
                ;;
              php)
                DOCROOT="public"
                [ -d "$DOCROOT" ] || DOCROOT="."
                start_cmd="php -S 0.0.0.0:${APP_PORT} -t \"$DOCROOT\""
                ;;
              *)
                if [ -f index.html ]; then
                  start_cmd="python -m http.server ${APP_PORT}"
                else
                  echo "[ERROR] Unknown project type and no static index.html to serve." | tee -a logs/deploy.log
                  exit 1
                fi
                ;;
            esac

            echo "[INFO] Starting application with: $start_cmd" | tee -a logs/deploy.log
            nohup bash -lc "$start_cmd" > logs/app.log 2>&1 & echo $! > app.pid

            echo "[INFO] Waiting up to 60s for port ${APP_PORT} to respond..." | tee -a logs/deploy.log
            for i in $(seq 1 60); do
              if command -v curl >/dev/null 2>&1; then
                if curl -fs "http://127.0.0.1:${APP_PORT}" >/dev/null 2>&1; then
                  echo "[INFO] Application is responding on port ${APP_PORT}" | tee -a logs/deploy.log
                  exit 0
                fi
              elif command -v nc >/dev/null 2>&1; then
                if nc -z 127.0.0.1 "${APP_PORT}" >/dev/null 2>&1; then
                  echo "[INFO] Application port ${APP_PORT} is open" | tee -a logs/deploy.log
                  exit 0
                fi
              else
                # Fallback: check process existence
                if [ -f app.pid ] && ps -p "$(cat app.pid)" >/dev/null 2>&1; then
                  echo "[INFO] Application process is running (PID $(cat app.pid))" | tee -a logs/deploy.log
                  exit 0
                fi
              fi
              sleep 1
            done

            echo "[ERROR] Application did not become ready on port ${APP_PORT}. Last 100 log lines:" | tee -a logs/deploy.log
            tail -n 100 logs/app.log || true
            exit 1
          '''
        }
      }
    }
  }

  post {
    always {
      script {
        sh '''
          set -Eeuo pipefail
          echo "---- Deployment summary ----"
          if [ -f app.pid ]; then
            PID="$(cat app.pid)"
            if ps -p "$PID" >/dev/null 2>&1; then
              echo "App running with PID $PID"
            else
              echo "App is not running."
            fi
          else
            echo "No PID file found."
          fi
        '''
      }
      archiveArtifacts artifacts: 'logs/*.log', allowEmptyArchive: true, onlyIfSuccessful: false
    }
  }
}