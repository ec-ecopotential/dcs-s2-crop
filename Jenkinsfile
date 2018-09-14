pipeline {

  options {
    buildDiscarder(logRotator(numToKeepStr: '5'))
  }

  environment {
        PATH="/opt/anaconda/bin:/opt/anaconda/bin:/usr/lib64/qt-3.3/bin:/usr/local/bin:/bin:/usr/bin:/usr/local/sbin:/usr/sbin:/sbin:/home/msagona/bin"
  }

  agent {
    node {
      label 'ci-community-docker'
    }
  }

  stages {

    stage('Package & Dockerize') {
      steps {
        withMaven( maven: 'apache-maven-3.0.5' ) {
            sh 'mvn -B deploy'
        }
      }
    }
  }
}
