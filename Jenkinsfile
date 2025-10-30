pipeline {
  agent any

  options {
    skipDefaultCheckout(true)
    timestamps()
    ansiColor('xterm')
    disableConcurrentBuilds()
    buildDiscarder(logRotator(numToKeepStr: '20', artifactNumToKeepStr: '10'))
    timeout(time: 60, unit: 'MINUTES')
  }

  parameters {
    choice(name: 'ENV', choices: ['dev', 'staging', 'prod'], description: 'Deployment environment')
    string(name: 'DEPLOY_TARGET', defaultValue: '', description: 'Target environment/host/cluster')
    booleanParam(name: 'RUN_TESTS', defaultValue: false, description: 'Run tests if available')
  }

  environment {
    APP_ENV = "${params.ENV}"
    DEPLOY_TARGET = "${params.DEPLOY_TARGET}"
  }

  stages {
    stage('Checkout from Git') {
      steps {
        checkout scm
        script {
          if (isUnix()) {
            sh 'git submodule update --init --recursive || true'
          } else {
            bat 'git submodule update --init --recursive || ver'
          }
        }
      }
    }

    stage('Environment setup') {
      steps {
        script {
          if (isUnix()) {
            sh '''
              echo "Environment: $APP_ENV"
              command -v bash >/dev/null 2>&1 || true
              command -v python3 >/dev/null 2>&1 || true
              command -v node >/dev/null 2>&1 || true
              command -v npm >/dev/null 2>&1 || true
              command -v mvn >/dev/null 2>&1 || true
              command -v gradle >/dev/null 2>&1 || true
              command -v go >/dev/null 2>&1 || true
              command -v cargo >/dev/null 2>&1 || true
              chmod +x mvnw gradlew || true
              corepack enable || true
            '''
          } else {
            bat """
              echo Environment: %APP_ENV%
              where python || ver
              where node || ver
              where npm || ver
              where mvn || ver
              where gradle || ver
              where go || ver
              where cargo || ver
            """
          }
        }
      }
    }

    stage('Install dependencies') {
      steps {
        script {
          // Node.js projects
          if (fileExists('package.json')) {
            echo 'Detected Node.js project'
            if (isUnix()) {
              if (fileExists('package-lock.json')) {
                sh 'npm ci'
              } else if (fileExists('yarn.lock')) {
                sh 'yarn install --frozen-lockfile || (corepack enable && yarn install --frozen-lockfile)'
              } else if (fileExists('pnpm-lock.yaml')) {
                sh 'pnpm install --frozen-lockfile || (corepack enable && pnpm install --frozen-lockfile)'
              } else {
                sh 'npm install'
              }
            } else {
              if (fileExists('package-lock.json')) {
                bat 'npm ci'
              } else if (fileExists('yarn.lock')) {
                bat 'yarn install --frozen-lockfile || (corepack enable && yarn install --frozen-lockfile)'
              } else if (fileExists('pnpm-lock.yaml')) {
                bat 'pnpm install --frozen-lockfile || (corepack enable && pnpm install --frozen-lockfile)'
              } else {
                bat 'npm install'
              }
            }
          }
          // Maven projects
          else if (fileExists('pom.xml') || fileExists('mvnw') || fileExists('mvnw.cmd')) {
            echo 'Detected Maven project'
            if (isUnix()) {
              if (fileExists('mvnw')) {
                sh './mvnw -B -ntp dependency:go-offline'
              } else {
                sh 'mvn -B -ntp dependency:go-offline'
              }
            } else {
              if (fileExists('mvnw.cmd')) {
                bat 'mvnw.cmd -B -ntp dependency:go-offline'
              } else {
                bat 'mvn -B -ntp dependency:go-offline'
              }
            }
          }
          // Gradle projects
          else if (fileExists('build.gradle') || fileExists('build.gradle.kts') || fileExists('gradlew') || fileExists('gradlew.bat')) {
            echo 'Detected Gradle project'
            if (isUnix()) {
              if (fileExists('gradlew')) {
                sh './gradlew --no-daemon help'
              } else {
                sh 'gradle --no-daemon help'
              }
            } else {
              if (fileExists('gradlew.bat')) {
                bat 'gradlew.bat --no-daemon help'
              } else {
                bat 'gradle --no-daemon help'
              }
            }
          }
          // Python projects
          else if (fileExists('requirements.txt') || fileExists('pyproject.toml') || fileExists('Pipfile')) {
            echo 'Detected Python project'
            if (isUnix()) {
              sh '''
                python3 -m venv .venv || true
                . .venv/bin/activate || true
                python3 -m pip install --upgrade pip setuptools wheel || true
                if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
                if [ -f Pipfile ]; then pip install pipenv && pipenv install --deploy --system; fi
                if [ -f pyproject.toml ]; then pip install . || pip install -e . || true; fi
              '''
            } else {
              bat '''
                python -m venv .venv
                call .venv\\Scripts\\activate
                python -m pip install --upgrade pip setuptools wheel
                if exist requirements.txt pip install -r requirements.txt
                if exist Pipfile ( pip install pipenv && pipenv install --deploy --system )
                if exist pyproject.toml ( pip install . || pip install -e . )
              '''
            }
          }
          // Go projects
          else if (fileExists('go.mod')) {
            echo 'Detected Go project'
            if (isUnix()) {
              sh 'go mod download'
            } else {
              bat 'go mod download'
            }
          }
          // Rust projects
          else if (fileExists('Cargo.toml')) {
            echo 'Detected Rust project'
            if (isUnix()) {
              sh 'cargo fetch'
            } else {
              bat 'cargo fetch'
            }
          }
          // .NET projects (basic detection)
          else if (fileExists('global.json')) {
            echo 'Detected potential .NET project (global.json present)'
            if (isUnix()) {
              sh 'dotnet --info || true'
              sh 'dotnet restore || true'
            } else {
              bat 'dotnet --info || ver'
              bat 'dotnet restore || ver'
            }
          }
          // Fallback
          else {
            echo 'No recognized dependency manifest found. Skipping dependency installation.'
          }
        }
      }
    }

    stage('Deploy application') {
      steps {
        script {
          if (isUnix()) {
            if (fileExists('scripts/deploy.sh')) {
              sh 'chmod +x scripts/deploy.sh || true'
              sh 'scripts/deploy.sh "$APP_ENV" "$DEPLOY_TARGET"'
            } else if (fileExists('Makefile')) {
              sh 'make deploy ENV="$APP_ENV" TARGET="$DEPLOY_TARGET"'
            } else {
              echo 'No deploy script found. Add scripts/deploy.sh or a Makefile deploy target.'
            }
          } else {
            if (fileExists('scripts\\deploy.ps1')) {
              bat 'powershell -NoProfile -ExecutionPolicy Bypass -File scripts\\deploy.ps1 -Env "%APP_ENV%" -Target "%DEPLOY_TARGET%"'
            } else if (fileExists('scripts\\deploy.bat')) {
              bat 'scripts\\deploy.bat %APP_ENV% %DEPLOY_TARGET%'
            } else {
              bat 'echo No deploy script found. Add scripts\\deploy.ps1 or scripts\\deploy.bat or Makefile target.'
            }
          }
        }
      }
    }
  }

  post {
    success {
      echo "Pipeline succeeded for ${APP_ENV}"
    }
    failure {
      echo "Pipeline failed for ${APP_ENV}"
    }
    always {
      echo 'Pipeline finished.'
    }
  }
}