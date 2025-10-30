pipeline {
  agent any

  options {
    buildDiscarder(logRotator(numToKeepStr: '20', artifactNumToKeepStr: '10'))
    disableConcurrentBuilds()
    timestamps()
    timeout(time: 30, unit: 'MINUTES')
    ansiColor('xterm')
  }

  parameters {
    string(name: 'GIT_REF', defaultValue: '', description: 'Optional git ref to checkout (branch/tag/SHA). Empty uses Jenkinsfile SCM ref.')
    choice(name: 'DEPLOY_ENV', choices: ['dev', 'staging', 'prod'], description: 'Target deployment environment')
    string(name: 'DEPLOY_COMMAND', defaultValue: '', description: 'Optional custom deploy command to execute')
    booleanParam(name: 'SKIP_DEPLOY', defaultValue: false, description: 'Skip the Deploy application stage')
    string(name: 'CREDENTIALS_ID', defaultValue: '', description: 'Optional Jenkins credentials ID for deploy token (Secret Text)')
  }

  environment {
    GIT_DEPTH = '3'
  }

  stages {
    stage('Checkout from Git') {
      steps {
        script {
          // Clean workspace for reproducibility
          deleteDir()
        }
        retry(2) {
          script {
            if (params.GIT_REF?.trim()) {
              // Fresh checkout with optional shallow clone and ref
              if (isUnix()) {
                sh """
                  set -euxo pipefail
                  git init .
                  git remote remove origin || true
                  git remote add origin "\${scm.userRemoteConfigs[0].url}"
                  git fetch --tags --prune --depth ${env.GIT_DEPTH} origin +refs/heads/*:refs/remotes/origin/* +refs/tags/*:refs/tags/*
                  git checkout -f "${params.GIT_REF}"
                """
              } else {
                bat """
                  @echo on
                  if exist .git rmdir /s /q .git
                  git init .
                  git remote remove origin 2>nul
                  git remote add origin "${scm.userRemoteConfigs[0].url}"
                  git fetch --tags --prune --depth ${env.GIT_DEPTH} origin +refs/heads/*:refs/remotes/origin/* +refs/tags/*:refs/tags/*
                  git checkout -f "${params.GIT_REF}"
                """
              }
            } else {
              // Use Jenkinsfile SCM context
              checkout scm
            }
          }
        }
        script {
          if (isUnix()) {
            sh 'git --no-pager log -1 --pretty=oneline || true'
          } else {
            bat 'git --no-pager log -1 --pretty=oneline || ver'
          }
        }
      }
    }

    stage('Environment setup') {
      steps {
        script {
          def run = { String cmd ->
            if (isUnix()) { sh label: "env: ${cmd}", script: cmd } else { bat label: "env: ${cmd}", script: cmd }
          }

          echo "Node: ${env.NODE_NAME}, Executor: ${env.EXECUTOR_NUMBER}, Workspace: ${env.WORKSPACE}"
          // Print basic tooling info if available (non-fatal)
          run('java -version || exit 0')
          run('node --version || exit 0')
          run('npm --version || exit 0')
          run('python --version || exit 0')
          run('pip --version || python -m pip --version || exit 0')
          run('mvn -v || exit 0')
          run('gradle -v || exit 0')
          run('go version || exit 0')
          run('rustc --version || exit 0')
          run('bundle -v || exit 0')
          run('composer -V || exit 0')

          // Ensure consistent line endings and safe git directory
          if (isUnix()) {
            sh '''
              git config --global core.autocrlf input || true
              git config --global --add safe.directory "$WORKSPACE" || true
            '''
          } else {
            bat '''
              git config --global core.autocrlf true
              git config --global --add safe.directory "%WORKSPACE%" 2>nul
            '''
          }
        }
      }
    }

    stage('Install dependencies') {
      steps {
        retry(2) {
          script {
            def run = { String cmd ->
              if (isUnix()) { sh label: "run: ${cmd}", script: cmd } else { bat label: "run: ${cmd}", script: cmd }
            }

            // Node.js
            if (fileExists('package-lock.json') || fileExists('npm-shrinkwrap.json') || fileExists('package.json')) {
              echo 'Detected Node.js project'
              run('npm ci --no-audit --prefer-offline || npm install')
            }
            // Maven
            else if (fileExists('pom.xml')) {
              echo 'Detected Maven project'
              run('mvn -B -ntp -DskipTests=true clean install')
            }
            // Gradle (prefer wrapper)
            else if (fileExists('gradlew') || fileExists('gradlew.bat') || fileExists('build.gradle') || fileExists('build.gradle.kts')) {
              echo 'Detected Gradle project'
              if (isUnix() && fileExists('gradlew')) {
                run('chmod +x gradlew')
                run('./gradlew --no-daemon build -x test')
              } else if (!isUnix() && fileExists('gradlew.bat')) {
                run('gradlew.bat --no-daemon build -x test')
              } else {
                run('gradle --no-daemon build -x test')
              }
            }
            // Python
            else if (fileExists('requirements.txt') || fileExists('pyproject.toml') || fileExists('Pipfile')) {
              echo 'Detected Python project'
              run('python -m pip install --upgrade pip setuptools wheel || exit 0')
              if (fileExists('requirements.txt')) {
                run('python -m pip install -r requirements.txt')
              } else if (fileExists('pyproject.toml')) {
                // Attempt PEP 517 build backends
                run('python -m pip install build || exit 0')
                run('python -m build || exit 0')
              } else if (fileExists('Pipfile')) {
                run('pip install pipenv || python -m pip install pipenv')
                run('pipenv install --dev')
              }
            }
            // Go
            else if (fileExists('go.mod')) {
              echo 'Detected Go project'
              run('go mod download')
              run('go build ./...')
            }
            // Rust
            else if (fileExists('Cargo.toml')) {
              echo 'Detected Rust project'
              run('cargo fetch')
              run('cargo build --release')
            }
            // Ruby
            else if (fileExists('Gemfile')) {
              echo 'Detected Ruby project'
              run('bundle config set path "vendor/bundle" || exit 0')
              run('bundle install --jobs=4 --retry=3')
            }
            // PHP Composer
            else if (fileExists('composer.json')) {
              echo 'Detected PHP project'
              run('composer install --no-interaction --no-progress --prefer-dist')
            }
            else {
              echo 'No recognized dependency files found. Skipping installation.'
            }
          }
        }
      }
    }

    stage('Deploy application') {
      when {
        expression { return !params.SKIP_DEPLOY }
      }
      steps {
        script {
          def run = { String cmd ->
            if (isUnix()) { sh label: "deploy: ${cmd}", script: cmd } else { bat label: "deploy: ${cmd}", script: cmd }
          }

          def doDeploy = {
            if (params.DEPLOY_COMMAND?.trim()) {
              echo "Executing custom deploy command"
              run(params.DEPLOY_COMMAND)
            } else if (isUnix() && fileExists('scripts/deploy.sh')) {
              sh 'chmod +x scripts/deploy.sh'
              run("scripts/deploy.sh ${params.DEPLOY_ENV}")
            } else if (!isUnix() && fileExists('scripts\\deploy.ps1')) {
              bat "powershell -NoProfile -ExecutionPolicy Bypass -File scripts\\deploy.ps1 -Environment ${params.DEPLOY_ENV}"
            } else {
              echo 'No deploy command or script found. Skipping deploy.'
            }
          }

          if (params.CREDENTIALS_ID?.trim()) {
            withCredentials([string(credentialsId: params.CREDENTIALS_ID, variable: 'DEPLOY_TOKEN')]) {
              echo 'Using provided deployment credentials'
              doDeploy()
            }
          } else {
            doDeploy()
          }
        }
      }
    }
  }

  post {
    success {
      echo "Build succeeded: ${env.JOB_NAME} #${env.BUILD_NUMBER}"
    }
    failure {
      echo "Build failed: ${env.JOB_NAME} #${env.BUILD_NUMBER}"
    }
    always {
      echo "Finished with status: ${currentBuild.currentResult}"
      // Remove workspace to avoid residue between builds
      deleteDir()
    }
  }
}