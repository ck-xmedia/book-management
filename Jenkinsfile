pipeline {
  agent { label 'linux' }

  environment {
    REPO_URL    = 'https://github.com/ck-xmedia/book-management.git'
    BRANCH_NAME = 'jenkins-automation-30'
    APP_PORT    = '8080'
    LOG_DIR     = "${WORKSPACE}/logs"
    APP_NAME    = 'book-management'
  }

  stages {
    stage('Checkout') {
      steps {
        deleteDir()
        git branch: env.BRANCH_NAME, url: env.REPO_URL
      }
    }

    stage('Install Dependencies') {
      steps {
        sh '''
          set -e
          mkdir -p "$LOG_DIR" data
          python3 -m venv .venv || python -m venv .venv
          . .venv/bin/activate
          pip install --upgrade pip
          pip install -r requirements.txt
        '''
      }
    }

    stage('Test') {
      steps {
        sh '''
          set -e
          . .venv/bin/activate
          if [ -f "pytest.ini" ] || [ -d "tests" ] || ls -1 test_*.py *_test.py >/dev/null 2>&1; then
            echo "Tests detected; running pytest."
            pytest -q
          else
            echo "No tests detected; skipping."
          fi
        '''
      }
    }

    stage('Deploy') {
      steps {
        sh '''
          set -e
          . .venv/bin/activate
          export PORT="${APP_PORT}"
          PID_FILE="/tmp/${APP_NAME}.pid"

          if [ -f "$PID_FILE" ]; then
            OLD_PID="$(cat "$PID_FILE" || true)"
            if [ -n "$OLD_PID" ] && ps -p "$OLD_PID" >/dev/null 2>&1; then
              echo "Stopping existing process $OLD_PID"
              kill "$OLD_PID" || true
              sleep 3
              if ps -p "$OLD_PID" >/dev/null 2>&1; then
                echo "Force killing $OLD_PID"
                kill -9 "$OLD_PID" || true
              fi
            fi
            rm -f "$PID_FILE"
          fi

          echo "Starting ${APP_NAME} on port ${APP_PORT}"
          nohup uvicorn app.main:app --host 0.0.0.0 --port "${APP_PORT}" --workers 1 > "${LOG_DIR}/app.out" 2> "${LOG_DIR}/app.err" &
          NEW_PID=$!
          echo "$NEW_PID" > "$PID_FILE"
          echo "Started ${APP_NAME} with PID ${NEW_PID}"
        '''
      }
    }
  }

  post {
    always {
      archiveArtifacts artifacts: 'logs/**', allowEmptyArchive: true
    }
  }
}