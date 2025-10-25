pipeline {
    agent any

    environment {
        PYTHON_VERSION = '3.11'
        PIP_CACHE_DIR = '~/.cache/pip'
        VENV_DIR = 'venv'
        DEPLOY_DIR = '/var/www/book-management'  // target deploy directory
        APP_PORT = '8181'
    }

    options {
        timestamps()
        timeout(time: 30, unit: 'MINUTES')
    }

    stages {
        stage('Environment Setup') {
            steps {
                script {
                    echo '🔍 Checking required environments...'

                    def pythonInstalled = false
                    def pythonVersionCorrect = false

                    try {
                        def pythonVersion = sh(
                            script: 'python3 --version',
                            returnStdout: true
                        ).trim()

                        echo "✅ Found Python: ${pythonVersion}"
                        pythonInstalled = true

                        def versionMatch = pythonVersion =~ /Python (\d+\.\d+\.\d+)/
                        if (versionMatch) {
                            def currentVersion = versionMatch[0][1]
                            def requiredVersion = PYTHON_VERSION

                            def currentParts = currentVersion.tokenize('.')
                            def requiredParts = requiredVersion.tokenize('.')

                            def versionOk = true
                            for (int i = 0; i < Math.min(currentParts.size(), requiredParts.size()); i++) {
                                if (currentParts[i].toInteger() < requiredParts[i].toInteger()) {
                                    versionOk = false
                                    break
                                } else if (currentParts[i].toInteger() > requiredParts[i].toInteger()) {
                                    break
                                }
                            }

                            if (versionOk) {
                                pythonVersionCorrect = true
                            }
                        }
                    } catch (Exception e) {
                        echo "❌ Python not found: ${e.message}"
                    }

                    if (!pythonInstalled || !pythonVersionCorrect) {
                        echo "📦 Installing Python ${PYTHON_VERSION}..."
                        try {
                            sh 'sudo apt-get update'
                            sh 'sudo add-apt-repository -y ppa:deadsnakes/ppa'
                            sh 'sudo apt-get update'
                            sh "sudo apt-get install -y python${PYTHON_VERSION} python${PYTHON_VERSION}-venv python${PYTHON_VERSION}-dev"
                            echo "✅ Python ${PYTHON_VERSION} installed successfully"
                        } catch (Exception e) {
                            error("Failed to install Python ${PYTHON_VERSION}: ${e.message}")
                        }
                    }
                }
            }
        }

        stage('Checkout') {
            steps {
                git branch: 'main', url: 'https://github.com/ck-xmedia/book-management.git'
            }
        }

        stage('Install Dependencies') {
            steps {
                sh """
                    python3 -m venv ${VENV_DIR}
                    . ${VENV_DIR}/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                """
            }
        }

        // 🚀 Deployment Stage
         stages {
                stage('Deploy on 8181') {
                    steps {
                        sh '''
                            cd /var/jenkins_home/workspace/book-management
                            python3 -m venv venv
                            . venv/bin/activate
                            pip install fastapi uvicorn
                            
                            pkill -f "uvicorn main:app" || true
                            nohup python -m uvicorn main:app --host 0.0.0.0 --port ${APP_PORT} > app.log 2>&1 &
                            
                            echo "✅ Try: http://143.1.1.128:${APP_PORT}/"
                        '''
                    }
                }
            }
    }

    post {
        always {
            cleanWs()
        }
        success {
            emailext (
                subject: "✅ Pipeline Success: ${currentBuild.fullDisplayName}",
                body: "The pipeline completed successfully and was deployed to ${DEPLOY_DIR}.",
                recipientProviders: [[$class: 'DevelopersRecipientProvider']]
            )
        }
        failure {
            emailext (
                subject: "❌ Pipeline Failed: ${currentBuild.fullDisplayName}",
                body: "The pipeline failed. Please check the build logs.",
                recipientProviders: [[$class: 'DevelopersRecipientProvider']]
            )
        }
    }
}
