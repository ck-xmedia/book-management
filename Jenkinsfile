pipeline {
  agent { label 'linux' }

  environment {
    REPO_URL    = 'https://github.com/ck-xmedia/book-management.git'
    BRANCH_NAME = 'jenkins-automation-25'
    APP_PORT    = '8080'
    LOG_DIR     = "${WORKSPACE}/logs"
    APP_NAME    = 'book-management'
  }

  options {
    timestamps()
    disableConcurrentBuilds()
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
          mkdir -p "$LOG_DIR"

          # Python dependencies
          if [ -f requirements.txt ]; then
            echo "Installing Python dependencies..."
            pip3 install -r requirements.txt
          fi

          # Node.js dependencies (if a Node app)
          if [ -f package.json ] && command -v npm >/dev/null 2>&1; then
            if [ -f package-lock.json ]; then
              echo "Installing Node.js dependencies with npm ci..."
              npm ci
            else
              echo "Installing Node.js dependencies with npm install..."
              npm install
            fi
          fi
        '''
      }
    }

    stage('Test') {
      steps {
        sh '''
          set -e

          # Python tests
          if [ -f requirements.txt ]; then
            if python3 -c "import pkgutil; import sys; sys.exit(0 if pkgutil.find_loader('pytest') else 1)" >/dev/null 2>&1; then
              if ls -1 **/test_*.py **/*_test.py >/dev/null 2>&1 || [ -d tests ]; then
                echo "Running Python tests..."
                python3 -m pytest -q
              else
                echo "No Python test files detected. Skipping."
              fi
            else
              echo "pytest not installed. Skipping Python tests."
            fi
          fi

          # Node.js tests
          if [ -f package.json ] && command -v node >/dev/null 2>&1 && command -v npm >/dev/null 2>&1; then
            if node -e "const p=require('./package.json');process.exit(!(p.scripts&&p.scripts.test));"; then
              echo "Running Node.js tests..."
              npm test --silent
            else
              echo "No npm test script. Skipping Node.js tests."
            fi
          fi
        '''
      }
    }

    stage('Deploy') {
      steps {
        sh '''
          set -e
          mkdir -p "$LOG_DIR"

          # Prefer direct Python (FastAPI/Uvicorn) deployment if available
          if [ -f requirements.txt ] && python3 -c "import pkgutil,sys; sys.exit(0 if pkgutil.find_loader('uvicorn') else 1)" >/dev/null 2>&1; then
            echo "Deploying Python FastAPI app with uvicorn..."

            # Stop previous process if running
            if [ -f "$LOG_DIR/app.pid" ]; then
              PID=$(cat "$LOG_DIR/app.pid" || true)
              if [ -n "$PID" ] && kill -0 "$PID" >/dev/null 2>&1; then
                echo "Stopping existing process PID=$PID"
                kill "$PID" || true
                sleep 3
                if kill -0 "$PID" >/dev/null 2>&1; then
                  echo "Force killing PID=$PID"
                  kill -9 "$PID" || true
                fi
              fi
            fi

            # Ensure data dir and env
            mkdir -p ./data
            if [ ! -f .env ] && [ -f .env.example ]; then
              cp .env.example .env
            fi

            # Start new process
            nohup uvicorn app.main:app --host 0.0.0.0 --port "$APP_PORT" --workers 1 > "$LOG_DIR/${APP_NAME}.out" 2> "$LOG_DIR/${APP_NAME}.err" &
            echo $! > "$LOG_DIR/app.pid"
            echo "Started uvicorn on port $APP_PORT with PID $(cat "$LOG_DIR/app.pid")"
            exit 0
          fi

          # Fallback: Node.js deployment via pm2 if present
          if [ -f package.json ] && command -v pm2 >/dev/null 2>&1; then
            echo "Deploying Node.js app with pm2..."
            # Determine start method: script file or npm start
            if node -e "const fs=require('fs');process.exit(fs.existsSync('server.js')?0:1)"; then
              pm2 delete "$APP_NAME" >/dev/null 2>&1 || true
              pm2 start server.js --name "$APP_NAME" --time -- --port "$APP_PORT"
            else
              if node -e "const p=require('./package.json');process.exit(!(p.scripts&&p.scripts.start));"; then
                pm2 delete "$APP_NAME" >/dev/null 2>&1 || true
                pm2 start npm --name "$APP_NAME" -- run start -- --port "$APP_PORT"
              else
                echo "No Node entry or start script found. Skipping pm2 deploy."
              fi
            end
            pm2 save || true
            exit 0
          fi

          echo "No recognized runtime for deployment. Skipping."
        '''
      }
    }
  }

  post {
    always {
      sh 'ls -lah "$LOG_DIR" || true'
      archiveArtifacts artifacts: 'logs/**/*', allowEmptyArchive: true
    }
  }
}