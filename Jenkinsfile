pipeline {
  agent any
  options {
    timestamps()
    skipDefaultCheckout(true)
  }
  environment {
    REPO_URL = 'https://github.com/ck-xmedia/book-management.git'
    REPO_BRANCH = 'jenkins-automation-19'
    APP_PORT = '8080'
    VENV_DIR = "${WORKSPACE}/.venv"
    DATA_DIR = "${WORKSPACE}/data"
    DOCKER_IMAGE_NAME = 'json-books:latest'
  }
  stages {
    stage('Checkout') {
      steps {
        git branch: "${REPO_BRANCH}", url: "${REPO_URL}"
      }
    }
    stage('Environment Setup') {
      steps {
        sh '''
          set -euxo pipefail
          echo "Workspace: $WORKSPACE"
          echo "Using app port: $APP_PORT"
          mkdir -p "$DATA_DIR"
          # Ensure .env present and configured
          if [ -f ".env" ]; then
            echo ".env exists"
          else
            if [ -f ".env.example" ]; then
              cp .env.example .env
            else
              touch .env
            fi
          fi
          # Ensure PORT set to APP_PORT
          if grep -q '^PORT=' .env; then
            sed -i "s/^PORT=.*/PORT=$APP_PORT/" .env
          else
            echo "PORT=$APP_PORT" >> .env
          fi
          echo "Final .env:"
          grep -E '^(PORT|DATA_DIR|DATA_FILE|DATA_LOCK_FILE|ENABLE_BACKUPS|BACKUP_EVERY_N_WRITES|CORS_ORIGINS|LOG_LEVEL|APP_ENV)=' .env || true
        '''
      }
    }
    stage('Install Dependencies') {
      steps {
        sh '''
          set -euxo pipefail
          FOUND=0

          if [ -f "requirements.txt" ]; then
            FOUND=1
            echo "Detected Python project (requirements.txt)"
            PY_BIN=""
            if command -v python3 >/dev/null 2>&1; then
              PY_BIN="python3"
            elif command -v python >/dev/null 2>&1; then
              PY_BIN="python"
            else
              echo "No python interpreter found on PATH."
              exit 1
            fi
            "$PY_BIN" --version || true
            "$PY_BIN" -m venv "$VENV_DIR"
            . "$VENV_DIR/bin/activate"
            python -m pip install --upgrade pip
            pip install -r requirements.txt
            python -c "import fastapi, uvicorn, pydantic, starlette; print('Python deps OK')" || true
          fi

          if [ -f "package.json" ]; then
            echo "Detected Node project (package.json)"
            if command -v npm >/dev/null 2>&1; then
              if [ -f "package-lock.json" ]; then
                npm ci
              else
                npm install
              fi
              echo "Node deps installed (if required by project)."
            else
              echo "npm not installed; skipping Node deps"
            fi
          fi

          if [ -f "pom.xml" ]; then
            FOUND=1
            echo "Detected Maven project"
            mvn -version || true
            mvn -B -DskipTests clean package
          fi

          if [ -f "build.gradle" ] || [ -f "build.gradle.kts" ]; then
            FOUND=1
            echo "Detected Gradle project"
            if [ -x "./gradlew" ]; then
              ./gradlew clean build -x test
            else
              gradle clean build -x test
            fi
          fi

          if [ $FOUND -eq 0 ]; then
            echo "No recognized backend dependency file found (continuing)."
          fi
        '''
      }
    }
    stage('Deploy Application') {
      steps {
        sh '''
          set -euxo pipefail
          mkdir -p run

          echo "Stopping any process or container on port ${APP_PORT}"

          # Kill processes on port
          if command -v lsof >/dev/null 2>&1; then
            PIDS=$(lsof -ti tcp:${APP_PORT} || true)
          else
            PIDS=$(fuser -n tcp ${APP_PORT} 2>/dev/null || true)
          fi
          if [ -n "${PIDS:-}" ]; then
            echo "Killing PIDs: ${PIDS}"
            kill -9 ${PIDS} || true
          else
            echo "No local processes bound to ${APP_PORT}"
          fi

          # Stop docker containers publishing the port
          if command -v docker >/dev/null 2>&1; then
            CONTAINERS_BY_PORT=$(docker ps --format '{{.ID}} {{.Ports}}' | awk '/0.0.0.0:'${APP_PORT}'->|:::'${APP_PORT}'->/ {print $1}')
            if [ -n "${CONTAINERS_BY_PORT:-}" ]; then
              echo "Stopping containers on ${APP_PORT}: ${CONTAINERS_BY_PORT}"
              docker stop ${CONTAINERS_BY_PORT} || true
              docker rm ${CONTAINERS_BY_PORT} || true
            fi
          fi

          # Deploy based on project structure
          if [ -f "requirements.txt" ] && [ -d "app" ]; then
            echo "Deploying as Python FastAPI app with uvicorn"
            # Activate venv if available and prefer venv uvicorn
            UVICORN_BIN="uvicorn"
            if [ -x "$VENV_DIR/bin/uvicorn" ]; then
              UVICORN_BIN="$VENV_DIR/bin/uvicorn"
            elif command -v uvicorn >/dev/null 2>&1; then
              UVICORN_BIN="$(command -v uvicorn)"
            else
              echo "uvicorn not found. Ensure Python deps stage succeeded."
              exit 1
            fi

            # Stop previous background app if tracked
            if [ -f run/app.pid ]; then
              OLD_PID=$(cat run/app.pid || true)
              if [ -n "${OLD_PID}" ] && kill -0 "${OLD_PID}" 2>/dev/null; then
                echo "Killing previous app pid ${OLD_PID}"
                kill -9 "${OLD_PID}" || true
              fi
            fi

            nohup "$UVICORN_BIN" "app.main:app" --host "0.0.0.0" --port "${APP_PORT}" --workers "1" > run/app.log 2>&1 &
            NEW_PID=$!
            echo "${NEW_PID}" > run/app.pid
            echo "Started uvicorn with PID ${NEW_PID}"

          elif [ -f "Dockerfile" ]; then
            echo "Deploying using Docker image build/run"
            if command -v docker >/dev/null 2>&1; then
              docker build -t "${DOCKER_IMAGE_NAME}" .
              # Use nohup for background and logging
              nohup bash -c "docker run --rm --env-file .env -p ${APP_PORT}:${APP_PORT} -v ${DATA_DIR}:/app/data ${DOCKER_IMAGE_NAME}" > run/docker.log 2>&1 &
              echo $! > run/docker.pid
              echo "Started dockerized app. PID $(cat run/docker.pid)"
            else
              echo "Docker not available. Cannot deploy via Docker."
              exit 1
            fi

          elif [ -f "package.json" ]; then
            echo "Detected Node app; attempting to run via npm start"
            if [ -f run/node.pid ]; then
              OLD_PID=$(cat run/node.pid || true)
              if [ -n "${OLD_PID}" ] && kill -0 "${OLD_PID}" 2>/dev/null; then
                echo "Killing previous node pid ${OLD_PID}"
                kill -9 "${OLD_PID}" || true
              fi
            fi

            if command -v npm >/dev/null 2>&1 && npm pkg get scripts.start >/dev/null 2>&1; then
              nohup npm start --if-present > run/node.log 2>&1 &
            elif [ -f "server.js" ]; then
              nohup node server.js > run/node.log 2>&1 &
            else
              echo "No start script or server.js found for Node project."
              exit 1
            fi
            echo $! > run/node.pid
            echo "Started Node app with PID $(cat run/node.pid)"

          else
            echo "Unable to determine deployment strategy."
            exit 1
          fi

          # Health check
          echo "Waiting for service on http://localhost:${APP_PORT}/healthz"
          STATUS=""
          for i in $(seq 1 30); do
            STATUS=$(curl -sS -o /dev/null -w "%{http_code}" "http://localhost:${APP_PORT}/healthz" || true)
            if [ "$STATUS" = "200" ]; then
              echo "Service is healthy."
              break
            else
              echo "Waiting (${i}/30)... last status: ${STATUS:-none}"
              sleep 2
            fi
          done
          if [ "$STATUS" != "200" ]; then
            echo "Health check failed after retries. Dumping recent logs..."
            (tail -n 200 run/*.log || true)
            exit 1
          fi
        '''
      }
    }
  }
  post {
    always {
      sh '''
        set -euxo pipefail
        ls -la run || true
        tail -n +200 run/*.log || true
      '''
      archiveArtifacts artifacts: 'run/*.log, run/*.pid, .env', allowEmptyArchive: true
    }
  }
}