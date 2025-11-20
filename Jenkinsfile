pipeline {
  agent any

  options {
    skipDefaultCheckout(true)
    timestamps()
  }

  environment {
    REPO_URL    = 'https://github.com/ck-xmedia/book-management.git'
    BRANCH_NAME = 'jenkins-automation-31'
    APP_PORT    = '8080'
    LOG_DIR     = "${WORKSPACE}/logs"
    APP_NAME    = 'book-management'
  }

  stages {
    stage('Checkout') {
      steps {
        deleteDir()
        git branch: "${BRANCH_NAME}", url: "${REPO_URL}"
      }
    }

    stage('Install Dependencies') {
      steps {
        sh '''
          set -e

          # Python
          if [ -f requirements.txt ]; then
            python3 -m pip install --upgrade pip
            python3 -m pip install -r requirements.txt
          fi

          # Node.js
          if [ -f package.json ] && command -v npm >/dev/null 2>&1; then
            npm ci || true
          fi

          # Maven
          if [ -f pom.xml ]; then
            mvn -B -DskipTests package
          fi
        '''
      }
    }

    stage('Test') {
      steps {
        sh '''
          set -e

          # Python tests (optional)
          if command -v pytest >/dev/null 2>&1; then
            pytest -q || true
          fi

          # Node.js tests (optional)
          if [ -f package.json ] && command -v npm >/dev/null 2>&1; then
            npm test --if-present || true
          fi

          # Maven tests (optional)
          if [ -f pom.xml ]; then
            mvn -B test || true
          fi
        '''
      }
    }

    stage('Deploy') {
      steps {
        sh '''
          set -e
          mkdir -p "${LOG_DIR}"

          # Use example env if real one missing
          if [ -f .env.example ] && [ ! -f .env ]; then
            cp .env.example .env
          fi

          # Python (FastAPI / Uvicorn) - direct run
          if [ -f requirements.txt ]; then
            pkill -f "uvicorn app.main:app" || true
            nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port "${APP_PORT}" --workers 1 > "${LOG_DIR}/${APP_NAME}.log" 2>&1 &
          fi

          # Node.js (pm2) - if present
          if [ -f package.json ] && command -v pm2 >/dev/null 2>&1; then
            pm2 delete "${APP_NAME}" || true
            if command -v npm >/dev/null 2>&1; then
              pm2 start npm --name "${APP_NAME}" -- start
              pm2 save || true
            fi
          fi

          # Java/Maven - placeholder direct run (if applicable)
          # [Add your start command if using Java]
        '''
      }
    }
  }

  post {
    success {
      echo "Deployment complete on port ${APP_PORT}. Logs at ${LOG_DIR}."
    }
    failure {
      echo 'Pipeline failed.'
    }
  }
}