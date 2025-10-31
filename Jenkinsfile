pipeline {
  agent any
  options {
    timestamps()
    disableConcurrentBuilds()
  }
  environment {
    REPO_URL   = 'https://github.com/ck-xmedia/book-management.git'
    BRANCH_NAME = 'jenkins-automation-26'
    APP_PORT   = '8080'
    VENV_DIR   = "${WORKSPACE}/.venv"
    LOG_DIR    = "${WORKSPACE}/logs"
    PID_FILE   = "${WORKSPACE}/app.pid"
    APP_ENTRY  = 'app.main:app'
    PYTHON_BIN = "${WORKSPACE}/.venv/bin/python"
    PIP_BIN    = "${WORKSPACE}/.venv/bin/pip"
  }
  stages {
    stage('Checkout') {
      steps {
        deleteDir()
        git branch: "${BRANCH_NAME}", url: "${REPO_URL}"
      }
    }

    stage('Environment Setup') {
      steps {
        sh '''
          set -euxo pipefail
          mkdir -p "${LOG_DIR}"

          PROJECT_TYPE="unknown"
          if [ -f requirements.txt ]; then PROJECT_TYPE="python"; fi
          if [ -f package.json ] && [ "${PROJECT_TYPE}" = "unknown" ]; then PROJECT_TYPE="node"; fi
          if [ -f pom.xml ]; then PROJECT_TYPE="maven"; fi

          echo "${PROJECT_TYPE}" > .project_type
          echo "Detected project type: $(cat .project_type)"
          echo "APP_PORT=${APP_PORT}" > .env.runtime || true
        '''
      }
    }

    stage('Install Dependencies') {
      steps {
        script {
          def ptype = sh(script: 'cat .project_type', returnStdout: true).trim()
          if (ptype == 'python') {
            sh '''
              set -euxo pipefail
              command -v python3 >/dev/null 2>&1 || { echo "python3 not found on PATH"; exit 1; }
              python3 -m venv "${VENV_DIR}"
              "${PIP_BIN}" install --upgrade pip
              test -f requirements.txt && "${PIP_BIN}" install -r requirements.txt
              "${PYTHON_BIN}" -c "import fastapi, uvicorn; print('fastapi', fastapi.__version__, 'uvicorn', uvicorn.__version__)"
            '''
          } else if (ptype == 'node') {
            sh '''
              set -euxo pipefail
              command -v node >/dev/null 2>&1 || { echo "node not found on PATH"; exit 1; }
              command -v npm  >/dev/null 2>&1 || { echo "npm not found on PATH"; exit 1; }
              npm ci
            '''
          } else if (ptype == 'maven') {
            sh '''
              set -euxo pipefail
              command -v mvn >/dev/null 2>&1 || { echo "maven not found on PATH"; exit 1; }
              mvn -B -ntp -DskipTests package
            '''
          } else {
            error "Unsupported project type: ${ptype}"
          }
        }
      }
    }

    stage('Deploy Application') {
      steps {
        script {
          def ptype = sh(script: 'cat .project_type', returnStdout: true).trim()
          if (ptype == 'python') {
            sh '''
              set -euxo pipefail

              echo "Killing existing process (PID file) if present..."
              if [ -f "${PID_FILE}" ]; then
                if kill -0 "$(cat ${PID_FILE})" >/dev/null 2>&1; then
                  kill -9 "$(cat ${PID_FILE})" || true
                fi
                rm -f "${PID_FILE}"
              fi

              echo "Freeing port ${APP_PORT}..."
              if command -v ss >/dev/null 2>&1; then
                PIDS="$(ss -ltnp 2>/dev/null | grep -E '[:\\.]'"${APP_PORT}"'\\b' | sed -n 's/.*pid=\\([0-9]\\+\\).*/\\1/p' | sort -u | tr '\\n' ' ')"
                [ -n "${PIDS}" ] && kill -9 ${PIDS} || true
              elif command -v fuser >/dev/null 2>&1; then
                fuser -k "${APP_PORT}/tcp" || true
              elif command -v lsof >/dev/null 2>&1; then
                lsof -ti :"${APP_PORT}" | xargs -r kill -9 || true
              elif command -v netstat >/dev/null 2>&1; then
                PID=$(netstat -tulpn 2>/dev/null | awk '/:'"${APP_PORT}"'\\b/ {print $7}' | cut -d/ -f1 | head -n1); [ -n "$PID" ] && kill -9 "$PID" || true
              else
                pkill -f "uvicorn.*${APP_PORT}" || true
              fi
              sleep 1

              echo "Starting FastAPI (uvicorn) in background on port ${APP_PORT}..."
              mkdir -p "${LOG_DIR}"
              nohup "${PYTHON_BIN}" -m uvicorn "${APP_ENTRY}" --host 0.0.0.0 --port "${APP_PORT}" --workers 1 > "${LOG_DIR}/app.out" 2> "${LOG_DIR}/app.err" &
              echo $! > "${PID_FILE}"

              sleep 2
              if ! kill -0 "$(cat ${PID_FILE})" >/dev/null 2>&1; then
                echo "Application failed to start. Last logs:"
                tail -n 200 "${LOG_DIR}/app.err" || true
                exit 1
              fi

              echo "Performing health check..."
              set +e
              ok=0
              for i in $(seq 1 30); do
                if command -v curl >/dev/null 2>&1; then
                  curl -sf "http://127.0.0.1:${APP_PORT}/healthz" >/dev/null && ok=1 && break
                elif command -v wget >/dev/null 2>&1; then
                  wget -qO- "http://127.0.0.1:${APP_PORT}/healthz" >/dev/null && ok=1 && break
                else
                  (echo > /dev/tcp/127.0.0.1/${APP_PORT}) >/dev/null 2>&1 && ok=1 && break
                fi
                sleep 1
              done
              set -e
              if [ "${ok}" -ne 1 ]; then
                echo "Health check failed."
                tail -n 200 "${LOG_DIR}/app.out" || true
                tail -n 200 "${LOG_DIR}/app.err" || true
                exit 1
              fi

              echo "Deployment successful and healthy on port ${APP_PORT}."
            '''
          } else if (ptype == 'node') {
            sh '''
              set -euxo pipefail

              echo "Freeing port ${APP_PORT}..."
              if command -v fuser >/dev/null 2>&1; then
                fuser -k "${APP_PORT}/tcp" || true
              elif command -v lsof >/dev/null 2>&1; then
                lsof -ti :"${APP_PORT}" | xargs -r kill -9 || true
              fi

              mkdir -p "${LOG_DIR}"
              if grep -q '"start"' package.json 2>/dev/null; then
                nohup npm run start --if-present > "${LOG_DIR}/app.out" 2> "${LOG_DIR}/app.err" &
              elif [ -f server.js ]; then
                nohup node server.js > "${LOG_DIR}/app.out" 2> "${LOG_DIR}/app.err" &
              else
                echo "No start script or server.js found for Node project"
                exit 1
              fi
              echo $! > "${PID_FILE}"
            '''
          } else if (ptype == 'maven') {
            sh '''
              set -euxo pipefail

              echo "Freeing port ${APP_PORT}..."
              if command -v fuser >/dev/null 2>&1; then
                fuser -k "${APP_PORT}/tcp" || true
              elif command -v lsof >/dev/null 2>&1; then
                lsof -ti :"${APP_PORT}" | xargs -r kill -9 || true
              fi

              mkdir -p "${LOG_DIR}"
              JAR_FILE=$(ls -1 target/*.jar | head -n1)
              [ -f "$JAR_FILE" ] || { echo "JAR not found in target/"; exit 1; }
              nohup java -jar "$JAR_FILE" --server.port="${APP_PORT}" > "${LOG_DIR}/app.out" 2> "${LOG_DIR}/app.err" &
              echo $! > "${PID_FILE}"
            '''
          } else {
            error "Unsupported project type for deployment: ${ptype}"
          }
        }
      }
    }
  }
  post {
    always {
      sh '''
        set -e
        echo "Build finished. Tail of error log (if any):"
        test -f "${LOG_DIR}/app.err" && tail -n 50 "${LOG_DIR}/app.err" || true
      '''
      archiveArtifacts artifacts: 'logs/**/*', fingerprint: true, allowEmptyArchive: true
    }
    success {
      echo "Application deployed on port ${APP_PORT}"
    }
    failure {
      echo 'Deployment failed.'
    }
  }
}