#!/usr/bin/env bash
set -euo pipefail

echo "[pw-agent] Starting socat localhost proxies to compose services..."
socat TCP-LISTEN:3000,fork,reuseaddr TCP:react:3000 &
socat TCP-LISTEN:4200,fork,reuseaddr TCP:angular:80 &
socat TCP-LISTEN:5173,fork,reuseaddr TCP:svelte:5173 &
socat TCP-LISTEN:8000,fork,reuseaddr TCP:backend:8000 &
socat TCP-LISTEN:8001,fork,reuseaddr TCP:vision-service:8001 &

echo "[pw-agent] Waiting for Jenkins controller at ${JENKINS_URL}..."
until curl -fs "${JENKINS_URL}/login" > /dev/null; do
  echo "[pw-agent] Jenkins not ready yet, retrying in 3s..."
  sleep 3
done

echo "[pw-agent] Downloading agent.jar from controller..."
curl -fsS -o /opt/agent.jar "${JENKINS_URL}/jnlpJars/agent.jar"

echo "[pw-agent] Fetching inbound secret for node '${JENKINS_AGENT_NAME}'..."
SECRET=$(curl -fsS -u "${JENKINS_ADMIN_ID}:${JENKINS_ADMIN_PASSWORD}" \
  "${JENKINS_URL}/computer/${JENKINS_AGENT_NAME}/jenkins-agent.jnlp" \
  | sed -n 's/.*<application-desc><argument>\([a-f0-9]*\)<\/argument>.*/\1/p')

if [ -z "${SECRET}" ]; then
  echo "[pw-agent] ERROR: Could not retrieve JNLP secret for ${JENKINS_AGENT_NAME}" >&2
  exit 1
fi

mkdir -p /home/jenkins/agent
echo "[pw-agent] Connecting inbound agent '${JENKINS_AGENT_NAME}' to ${JENKINS_URL}..."
exec java -jar /opt/agent.jar \
  -url "${JENKINS_URL}" \
  -name "${JENKINS_AGENT_NAME}" \
  -secret "${SECRET}" \
  -workDir /home/jenkins/agent

