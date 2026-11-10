pipelineJob('harvest-templates') {
  description('1. Cosecha automatizada de plantillas visuales UI (templates/) por Frontend y generación de catálogo visual auditable en Artifacts.')
  properties {
    disableConcurrentBuilds()
  }
  parameters {
    choiceParam('FRONTEND', ['ALL', 'react', 'angular', 'svelte'], 'Frontend objetivo del cual cosechar plantillas visuales (o ALL para los tres)')
    stringParam('PRODUCT', 'basketball', 'Producto base a descomponer en product-card/ y cart-item/')
    booleanParam('HEADED', false, 'Abrir navegador visible en pantalla durante la cosecha (--headed)')
  }
  definition {
    cps {
      sandbox(true)
      script('''
        node('playwright') {
          def pwDir = env.PLAYWRIGHT_DIR ?: (isUnix() ? '/workspace/automation-playwright' : 'c:/TF/Trabajo-Final/automation-playwright')
          dir(pwDir) {
            load 'ci/Jenkinsfile.harvest'
          }
        }
      '''.stripIndent())
    }
  }
}

pipelineJob('run-e2e-tests') {
  description('2. Ejecutor de pruebas E2E parametrizado por Estrategia y Frontend. Publica JUnit, el reporte de Auditoría Visual OpenVisor por test y sincroniza la telemetría en metrics-history/.')
  properties {
    disableConcurrentBuilds()
  }
  parameters {
    choiceParam('STRATEGY', ['base', 'getby', 'opencv', 'getby_full', 'opencv_full', 'ALL'], 'Estrategia de localización a ejecutar (o ALL para todas)')
    choiceParam('FRONTEND', ['react', 'angular', 'svelte', 'ALL'], 'Aplicación frontend objetivo (o ALL para los tres frameworks)')
    choiceParam('REPEAT', ['1', '3', '5'], 'Cantidad de repeticiones seriales por celda')
    booleanParam('WARMUP', true, 'Precargar EasyOCR en vision-service antes de medir tiempos de las estrategias opencv / opencv_full')
    booleanParam('HEADED', false, 'Ejecutar el navegador con interfaz gráfica visible en pantalla (--headed)')
  }
  definition {
    cps {
      sandbox(true)
      script('''
        node('playwright') {
          def pwDir = env.PLAYWRIGHT_DIR ?: (isUnix() ? '/workspace/automation-playwright' : 'c:/TF/Trabajo-Final/automation-playwright')
          dir(pwDir) {
            load 'ci/Jenkinsfile.test'
          }
        }
      '''.stripIndent())
    }
  }
}

pipelineJob('historical-dashboard') {
  description('3. Consolida las últimas K ejecuciones históricas de metrics-history/ por estrategia y frontend y genera el Dashboard Estadístico y Científico (5 gráficos) sin abrir el navegador.')
  properties {
    disableConcurrentBuilds()
  }
  parameters {
    choiceParam('WINDOW_SIZE', ['3', '5', '10', '20'], 'Cantidad de últimas ejecuciones (K) por celda (estrategia, frontend) a consolidar')
  }
  definition {
    cps {
      sandbox(true)
      script('''
        node('playwright') {
          def pwDir = env.PLAYWRIGHT_DIR ?: (isUnix() ? '/workspace/automation-playwright' : 'c:/TF/Trabajo-Final/automation-playwright')
          dir(pwDir) {
            load 'ci/Jenkinsfile.historical'
          }
        }
      '''.stripIndent())
    }
  }
}

pipelineJob('benchmark') {
  description('Pipeline monolítico original (Test Runner + Dashboard de la corrida actual). Conservado por compatibilidad.')
  properties {
    disableConcurrentBuilds()
  }
  parameters {
    choiceParam('STRATEGY', ['base', 'getby', 'opencv', 'getby_full', 'opencv_full', 'ALL'], 'Estrategia de localización a evaluar (o ALL para matriz completa)')
    choiceParam('FRONTEND', ['react', 'angular', 'svelte', 'ALL'], 'Aplicación frontend objetivo (o ALL para los tres frameworks)')
    choiceParam('REPEAT', ['1', '3', '5'], 'Cantidad de repeticiones seriales por celda')
    booleanParam('WARMUP', true, 'Precargar EasyOCR en vision-service antes de medir tiempos de las estrategias opencv / opencv_full')
    booleanParam('HEADED', false, 'Ejecutar el navegador con interfaz gráfica visible en pantalla (--headed)')
  }
  definition {
    cps {
      sandbox(true)
      script('''
        node('playwright') {
          def pwDir = env.PLAYWRIGHT_DIR ?: (isUnix() ? '/workspace/automation-playwright' : 'c:/TF/Trabajo-Final/automation-playwright')
          dir(pwDir) {
            load 'ci/Jenkinsfile'
          }
        }
      '''.stripIndent())
    }
  }
}

pipelineJob('smoke') {
  description('Verifica conectividad del agente playwright y ejecuta la suite base sobre React.')
  properties {
    disableConcurrentBuilds()
  }
  parameters {
    booleanParam('HEADED', false, 'Ejecutar el navegador con interfaz gráfica visible en pantalla (--headed)')
  }
  definition {
    cps {
      sandbox(true)
      script('''
        node('playwright') {
          def pwDir = env.PLAYWRIGHT_DIR ?: (isUnix() ? '/workspace/automation-playwright' : 'c:/TF/Trabajo-Final/automation-playwright')
          dir(pwDir) {
            boolean isHeaded = (params.HEADED != null) ? params.HEADED.toBoolean() : false
            def headedArgs = isHeaded ? '--headed --slowmo=250' : ''
            try {
              stage('Healthchecks') {
                if (isUnix()) {
                  sh 'python ci/wait_for_services.py'
                } else {
                  bat 'python ci/wait_for_services.py'
                }
              }
              stage('Smoke Test (base + react)') {
                catchError(buildResult: 'UNSTABLE', stageResult: 'FAILURE') {
                  def cmd = "pytest tests/test_products.py -m base --env react --junitxml=reports/smoke/junit.xml ${headedArgs}".trim()
                  if (isUnix()) {
                    sh cmd
                  } else {
                    bat cmd
                  }
                }
              }
            } finally {
              stage('Publish JUnit & Artifacts') {
                junit testResults: 'reports/smoke/junit.xml', allowEmptyResults: true, keepProperties: true
                archiveArtifacts artifacts: 'reports/smoke/**/*.xml, reports/base/react/screenshots/*.png', allowEmptyArchive: true
              }
            }
          }
        }
      '''.stripIndent())
    }
  }
}
