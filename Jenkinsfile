pipeline {
  agent any
  options {
    timestamps()
    ansiColor('xterm')
    buildDiscarder(logRotator(numToKeepStr: '20', artifactNumToKeepStr: '10'))
    disableConcurrentBuilds()
    timeout(time: 30, unit: 'MINUTES')
  }
  environment {
    REPO_URL   = 'https://github.com/ck-xmedia/book-management.git'
    GIT_BRANCH = 'jenkins-automation-18'
    APP_PORT   = '8080'
    VENV_DIR   = "${WORKSPACE}/.venv"
    LOG_FILE   = "${WORKSPACE}/app.log"
    PID_FILE   = "${WORKSPACE}/app.pid"
    APP_ENTRY  = 'app.main:app'
    PROJECT_TYPE = ''
    HAS_DOCKERFILE = 'false'
  }
  stages {
    stage('Checkout') {
      steps {
        deleteDir()
        git branch: 'jenkins-automation-18', url: 'https://github.com/ck-xmedia/book-management.git'
      }
    }
    stage('Environment Setup') {
      steps {
        script {
          env.HAS_DOCKERFILE = fileExists('Dockerfile') ? 'true' : 'false'
          if (fileExists('requirements.txt')) {
            env.PROJECT_TYPE = 'python'
          } else if (fileExists('package.json')) {
            env.PROJECT_TYPE = 'node'
          } else if (fileExists('pom.xml')) {
            env.PROJECT_TYPE = 'maven'
          } else if (fileExists('build.gradle') || fileExists('build.gradle.kts')) {
            env.PROJECT_TYPE = 'gradle'
          } else {
            env.PROJECT_TYPE = 'unknown'
          }
          echo "Detected project type: ${env.PROJECT_TYPE} (Dockerfile: ${env.HAS_DOCKERFILE})"
        }
        sh '''
          set -eux
          mkdir -p "$WORKSPACE/data"
          if [ -f ".env.example" ] && [ ! -f ".env" ]; then cp .env.example .env; fi
        '''
      }
    }
    stage('Install Dependencies') {
      steps {
        script {
          if (!env.PROJECT_TYPE || env.PROJECT_TYPE.trim() == '' || env.PROJECT_TYPE == 'unknown') {
            if (fileExists('requirements.txt')) {
              env.PROJECT_TYPE = 'python'
            } else if (fileExists('package.json')) {
              env.PROJECT_TYPE = 'node'
            } else if (fileExists('pom.xml')) {
              env.PROJECT_TYPE = 'maven'
            } else if (fileExists('build.gradle') || fileExists('build.gradle.kts')) {
              env.PROJECT_TYPE = 'gradle'
            } else {
              env.PROJECT_TYPE = 'unknown'
            }
            echo "Re-detected project type: ${env.PROJECT_TYPE}"
          }

          if (env.PROJECT_TYPE == 'python') {
            sh '''
              set -eux
              command -v python3 >/dev/null 2>&1 || { echo "python3 not found"; exit 1; }
              python3 -m venv "$VENV_DIR"
              "$VENV_DIR/bin/pip" install --upgrade pip
              if [ -f requirements.txt ]; then
                "$VENV_DIR/bin/pip" install -r requirements.txt
              fi
              "$VENV_DIR/bin/python" -c "import fastapi,uvicorn; print('Python deps OK')" || true
            '''
          } else if (env.PROJECT_TYPE == 'node') {
            sh '''
              set -eux
              command -v npm >/dev/null 2>&1 || { echo "npm not found"; exit 1; }
              if [ -f package-lock.json ]; then npm ci; else npm install; fi
            '''
          } else if (env.PROJECT_TYPE == 'maven') {
            sh '''
              set -eux
              command -v mvn >/dev/null 2>&1 || { echo "maven not found"; exit 1; }
              mvn -B -DskipTests clean package
            '''
          } else if (env.PROJECT_TYPE == 'gradle') {
            sh '''
              set -eux
              if command -v gradle >/dev/null 2>&1; then
                gradle clean build -x test
              else
                chmod +x ./gradlew 2>/dev/null || true
                ./gradlew clean build -x test
              fi
            '''
          } else {
            echo 'Project type still unknown; defaulting to python due to presence of FastAPI/Dockerfile hints (if any).'
            sh '''
              set -eux
              if [ -f requirements.txt ]; then
                command -v python3 >/dev/null 2>&1 || { echo "python3 not found"; exit 1; }
                python3 -m venv "$VENV_DIR"
                "$VENV_DIR/bin/pip" install --upgrade pip
                "$VENV_DIR/bin/pip" install -r requirements.txt
              else
                echo "requirements.txt not found; cannot proceed"; exit 1
              fi
            '''
            env.PROJECT_TYPE = 'python'
          }
        }
      }
    }
    stage('Deploy Application') {
      steps {
        script {
          if (!env.PROJECT_TYPE || env.PROJECT_TYPE.trim() == '' || env.PROJECT_TYPE == 'unknown') {
            if (fileExists('requirements.txt')) {
              env.PROJECT_TYPE = 'python'
            } else if (fileExists('package.json')) {
              env.PROJECT_TYPE = 'node'
            } else if (fileExists('pom.xml')) {
              env.PROJECT_TYPE = 'maven'
            } else if (fileExists('build.gradle') || fileExists('build.gradle.kts')) {
              env.PROJECT_TYPE = 'gradle'
            } else {
              env.PROJECT_TYPE = 'unknown'
            }
            echo "Deploy-time project type: ${env.PROJECT_TYPE}"
          }

          // Ensure the target port is free; if not, select a fallback free port
          sh '''
            set -euo pipefail
            PORT="$APP_PORT"

            is_port_free() {
              if [ -x "$VENV_DIR/bin/python" ]; then
                "$VENV_DIR/bin/python" - "$PORT" <<'PY'
import socket, sys
port = int(sys.argv[1])
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.settimeout(0.2)
    sys.exit(0 if s.connect_ex(("127.0.0.1", port)) != 0 else 1)
PY
                return $?
              elif command -v python3 >/dev/null 2>&1; then
                python3 - "$PORT" <<'PY'
import socket, sys
port = int(sys.argv[1])
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.settimeout(0.2)
    sys.exit(0 if s.connect_ex(("127.0.0.1", port)) != 0 else 1)
PY
                return $?
              else
                (echo > /dev/tcp/127.0.0.1/"$PORT") >/dev/null 2>&1
                [ $? -eq 0 ] && return 1 || return 0
              fi
            }

            set +e
            if command -v lsof >/dev/null 2>&1; then
              PIDS="$(lsof -t -iTCP -sTCP:LISTEN -i :"$PORT" 2>/dev/null | tr '\\n' ' ')"
              [ -n "$PIDS" ] && kill -9 $PIDS 2>/dev/null || true
            fi
            if command -v fuser >/dev/null 2>&1; then
              fuser -k -n tcp "$PORT" 2>/dev/null || true
            fi
            if command -v ss >/dev/null 2>&1; then
              PIDS="$(ss -ltnp 2>/dev/null | awk -v p=":$PORT" '$4 ~ p {gsub(/pid=/,"",$7); split($7,a,","); split(a[1],b,"/"); print b[1]}' | tr '\\n' ' ')"
              [ -n "$PIDS" ] && kill -9 $PIDS 2>/dev/null || true
            fi
            if command -v netstat >/dev/null 2>&1; then
              PIDS="$(netstat -tulnp 2>/dev/null | awk -v p=":$PORT" '$4 ~ p {split($7,a,"/"); print a[1]}' | tr -d ' ')"
              [ -n "$PIDS" ] && kill -9 $PIDS 2>/dev/null || true
            fi
            if command -v pkill >/dev/null 2>&1; then
              pkill -f "uvicorn.*--port[= ]*$PORT" 2>/dev/null || true
            fi

            if [ -f "$PID_FILE" ]; then
              OLD_PID="$(cat "$PID_FILE" 2>/dev/null || true)"
              if [ -n "$OLD_PID" ] && kill -0 "$OLD_PID" 2>/dev/null; then
                kill "$OLD_PID" 2>/dev/null || true
                sleep 1
                kill -9 "$OLD_PID" 2>/dev/null || true
              fi
              rm -f "$PID_FILE" 2>/dev/null || true
            fi

            i=0
            while [ $i -lt 10 ]; do
              if is_port_free; then
                break
              fi
              i=$((i+1))
              sleep 1
            done

            if ! is_port_free; then
              echo "Port $PORT still in use; selecting a free fallback port."
              if [ -x "$VENV_DIR/bin/python" ]; then
                NEW_PORT="$("$VENV_DIR/bin/python" - <<'PY'
import socket
with socket.socket() as s:
    s.bind(('', 0))
    print(s.getsockname()[1])
PY
)"
              elif command -v python3 >/dev/null 2>&1; then
                NEW_PORT="$(python3 - <<'PY'
import socket
with socket.socket() as s:
    s.bind(('', 0))
    print(s.getsockname()[1])
PY
)"
              else
                NEW_PORT="$PORT"
              fi
              [ -z "$NEW_PORT" ] && NEW_PORT="$PORT"
              echo "$NEW_PORT" > .selected_port
            else
              echo "$PORT" > .selected_port
            fi
            set -e
          '''

          env.APP_PORT = readFile('.selected_port').trim()
          echo "Using application port: ${env.APP_PORT}"

          if (env.PROJECT_TYPE == 'python') {
            sh '''
              set -eux
              : > "$LOG_FILE"
              nohup "$VENV_DIR/bin/uvicorn" "$APP_ENTRY" --host 0.0.0.0 --port "$APP_PORT" --workers 1 >> "$LOG_FILE" 2>&1 &
              echo $! > "$PID_FILE"
              sleep 3
              if ! kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
                echo "Application failed to start. Tail of log:"
                tail -n 200 "$LOG_FILE" || true
                exit 1
              fi
              echo "Application started on port $APP_PORT with PID $(cat "$PID_FILE")"
            '''
          } else if (env.PROJECT_TYPE == 'node') {
            sh '''
              set -eux
              : > "$LOG_FILE"
              if [ -f package.json ] && grep -q '"start"' package.json; then
                nohup npm run start >> "$LOG_FILE" 2>&1 &
              else
                echo "No npm start script defined"; exit 1
              fi
              echo $! > "$PID_FILE"
              sleep 3
            '''
          } else if (env.PROJECT_TYPE == 'maven' || env.PROJECT_TYPE == 'gradle') {
            sh '''
              set -eux
              ARTIFACT_JAR=$(find . -type f -name "*.jar" | head -n1 || true)
              if [ -z "$ARTIFACT_JAR" ]; then
                echo "No JAR artifact found to run"; exit 1;
              fi
              : > "$LOG_FILE"
              nohup java -jar "$ARTIFACT_JAR" --server.port="$APP_PORT" >> "$LOG_FILE" 2>&1 &
              echo $! > "$PID_FILE"
              sleep 5
            '''
          } else {
            if (fileExists('requirements.txt')) {
              echo 'Unknown project type at deploy-time; defaulting to python.'
              sh '''
                set -eux
                : > "$LOG_FILE"
                nohup "$VENV_DIR/bin/uvicorn" "$APP_ENTRY" --host 0.0.0.0 --port "$APP_PORT" --workers 1 >> "$LOG_FILE" 2>&1 &
                echo $! > "$PID_FILE"
                sleep 3
                if ! kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
                  echo "Application failed to start. Tail of log:"
                  tail -n 200 "$LOG_FILE" || true
                  exit 1
                fi
              '''
            } else {
              error('Deployment not implemented for detected project type.')
            }
          }
          sh '''
            set +e
            OK=0
            if command -v curl >/dev/null 2>&1; then
              curl -fsS "http://127.0.0.1:$APP_PORT/healthz" || curl -fsS "http://127.0.0.1:$APP_PORT" || OK=1
            elif command -v wget >/dev/null 2>&1; then
              wget -qO- "http://127.0.0.1:$APP_PORT/healthz" >/dev/null || wget -qO- "http://127.0.0.1:$APP_PORT" >/dev/null || OK=1
            else
              echo "No curl/wget available to perform health check"
            fi
            if [ "$OK" -eq 1 ]; then
              echo "Health check failed"
              tail -n 200 "$LOG_FILE" || true
              exit 1
            fi
            set -e
          '''
        }
      }
    }
  }
  post {
    always {
      echo "Archiving logs and environment info"
      sh '''
        set +e
        echo "PROJECT_TYPE=$PROJECT_TYPE" > deploy.env
        echo "APP_PORT=$APP_PORT" >> deploy.env
        echo "VENV_DIR=$VENV_DIR" >> deploy.env
        tail -n 200 "$LOG_FILE" > app.tail.log 2>/dev/null || true
        set -e
      '''
      archiveArtifacts artifacts: 'app.log, app.tail.log, deploy.env', onlyIfSuccessful: false, allowEmptyArchive: true

      sh '''
        set +e
        if [ -f "$PID_FILE" ]; then
          PID="$(cat "$PID_FILE" 2>/dev/null || true)"
          if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
            echo "Stopping app PID $PID"
            kill "$PID" 2>/dev/null || true
            sleep 1
            kill -9 "$PID" 2>/dev/null || true
          fi
        fi
        PORT="$APP_PORT"
        if command -v fuser >/dev/null 2>&1; then
          fuser -k -n tcp "$PORT" 2>/dev/null || true
        fi
        if command -v lsof >/dev/null 2>&1; then
          P="$(lsof -t -iTCP -sTCP:LISTEN -i :"$PORT" 2>/dev/null | tr '\\n' ' ')"
          [ -n "$P" ] && kill -9 $P 2>/dev/null || true
        fi
        set -e
      '''
    }
    failure {
      echo "Build failed. Check archived logs."
    }
    success {
      echo "Deployment successful on port ${env.APP_PORT}"
    }
  }
}