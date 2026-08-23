pipeline {
    agent any

    environment {
        // Use the virtual environment path inside the workspace
        VENV_DIR = "venv"
        PYTHON = "${WORKSPACE}\\${VENV_DIR}\\Scripts\\python.exe"
        PIP = "${WORKSPACE}\\${VENV_DIR}\\Scripts\\pip.exe"
        PYTEST = "${WORKSPACE}\\${VENV_DIR}\\Scripts\\pytest.exe"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Setup Environment') {
            steps {
                bat """
                if not exist "${VENV_DIR}" (
                    python -m venv ${VENV_DIR}
                )
                """
            }
        }

        stage('Install Dependencies') {
            steps {
                bat """
                ${PIP} install --upgrade pip
                ${PIP} install -r requirements.txt
                ${PIP} install pytest httpx
                """
            }
        }

        stage('Run Tests') {
            steps {
                bat """
                set PYTHONPATH=${WORKSPACE}
                ${PYTEST} tests/ --junitxml=test-results.xml
                """
            }
        }
    }

    post {
        always {
            junit 'test-results.xml'
        }
        success {
            echo "Pipeline completed successfully!"
        }
        failure {
            echo "Pipeline failed! Please check the logs."
        }
    }
}
