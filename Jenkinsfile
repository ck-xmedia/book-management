pipeline {
  agent { label 'linux' }

  environment {
    REPO_URL    = 'https://github.com/ck-xmedia/book-management.git'
    BRANCH_NAME = 'jenkins-automation-29'
    APP_PORT    = '8080'
    LOG_DIR     = "${WORKSPACE}/logs"
    APP_NAME    = 'book-management'
  }

  stages {
    stage('Checkout') {
      steps {
        deleteDir()
        git url: env.REPO_URL, branch: env.BRANCH_NAME
      }
    }

    stage('Install Dependencies') {
      steps {
        sh '''
          set -e
          python3 -V
          python3 -m venv .venv || true
          ./.venv/bin/pip install --upgrade pip
          ./.venv/bin/pip install -r requirements.txt
          mkdir -p "${LOG_DIR}"
        '''
      }
    }

    stage('Test') {
      when {
        expression { return fileExists('tests') }
      }
      steps {
        sh '''
          set -e
          ./.venv/bin/pytest -q --maxfail=1
        '''
      }
    }

    stage('Deploy') {
      steps {
        sh '''
          set -e
          mkdir -p data
          [ -f ".env" ] || ([ -f ".env.example" ] && cp .env.example .env) || true

          if [ -f ".app.pid" ]; then
            if ps -p "$(cat .app.pid)" > /dev/null 2>&1; then
              echo "Stopping existing process $(cat .app.pid)"
              kill "$(cat .app.pid)" || true
              sleep 2
            fi
            rm -f .app.pid
          fi

          nohup ./.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port "${APP_PORT}" --workers 1 > "${LOG_DIR}/${APP_NAME}.log" 2>&1 &
          echo $! > .app.pid
          sleep 2
          if curl -sf "http://localhost:${APP_PORT}/healthz" > /dev/null 2>&1; then
            echo "Service healthy on port ${APP_PORT}"
          else
            echo "Warning: health check failed" >&2
          fi
        '''
      }
    }
  }

  post {
    always {
      archiveArtifacts artifacts: 'logs/*.log', onlyIfSuccessful: false, allowEmptyArchive: true
    }
  }
}