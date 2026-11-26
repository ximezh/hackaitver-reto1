#!/usr/bin/env bash
# Crea la instancia EC2 de CEDIS Flow (A-14): Ubuntu 24.04, grupo de seguridad mínimo e IP fija.
# Requiere AWS CLI v2 con credenciales de la cuenta del equipo (supuesto S-05).
#
#   REGION=us-east-1 CLAVE=<par-de-claves> IP_ADMIN=<tu-ip> ./crear-instancia.sh
#
# Variables:
#   REGION     región de AWS (obligatoria)
#   CLAVE      nombre de un par de claves EC2 ya creado, para entrar por SSH (obligatoria)
#   IP_ADMIN   IP pública desde la que se permite SSH (obligatoria). Nadie más entra por SSH:
#              la instancia se actualiza sola consultando el repositorio (DO-13).
#   TIPO       tipo de instancia (por defecto t3.small)
#   DISCO_GB   tamaño del disco raíz (por defecto 30)
#
# Crea recursos con costo. Si ya existe una instancia con la etiqueta Name=reto1, no hace nada.
set -euo pipefail

: "${REGION:?Falta REGION}"
: "${CLAVE:?Falta CLAVE}"
: "${IP_ADMIN:?Falta IP_ADMIN}"
TIPO="${TIPO:-t3.small}"
DISCO_GB="${DISCO_GB:-30}"
NOMBRE="reto1"
AQUI="$(cd "$(dirname "$0")" && pwd)"
export AWS_REGION="$REGION"

existente=$(aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=$NOMBRE" "Name=instance-state-name,Values=pending,running,stopped" \
  --query 'Reservations[].Instances[].InstanceId' --output text)
if [[ -n "$existente" ]]; then
  echo "Ya existe la instancia $existente con Name=$NOMBRE. No se crea otra."
  exit 0
fi

ami=$(aws ssm get-parameter \
  --name /aws/service/canonical/ubuntu/server/24.04/stable/current/amd64/hvm/ebs-gp3/ami-id \
  --query 'Parameter.Value' --output text)

vpc=$(aws ec2 describe-vpcs --filters Name=isDefault,Values=true --query 'Vpcs[0].VpcId' --output text)

grupo=$(aws ec2 describe-security-groups \
  --filters "Name=group-name,Values=$NOMBRE" "Name=vpc-id,Values=$vpc" \
  --query 'SecurityGroups[0].GroupId' --output text)
if [[ "$grupo" == "None" ]]; then
  grupo=$(aws ec2 create-security-group --group-name "$NOMBRE" --vpc-id "$vpc" \
    --description "CEDIS Flow: HTTP, HTTPS y SSH de administración" --query GroupId --output text)
  aws ec2 authorize-security-group-ingress --group-id "$grupo" --protocol tcp --port 80 --cidr 0.0.0.0/0
  aws ec2 authorize-security-group-ingress --group-id "$grupo" --protocol tcp --port 443 --cidr 0.0.0.0/0
  aws ec2 authorize-security-group-ingress --group-id "$grupo" --protocol tcp --port 22 --cidr "$IP_ADMIN/32"
fi

instancia=$(aws ec2 run-instances \
  --image-id "$ami" --instance-type "$TIPO" --key-name "$CLAVE" \
  --security-group-ids "$grupo" \
  --block-device-mappings "DeviceName=/dev/sda1,Ebs={VolumeSize=$DISCO_GB,VolumeType=gp3,Encrypted=true}" \
  --metadata-options "HttpTokens=required" \
  --user-data "file://$AQUI/cloud-init.yaml" \
  --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$NOMBRE}]" \
  --query 'Instances[0].InstanceId' --output text)

aws ec2 wait instance-running --instance-ids "$instancia"

asignacion=$(aws ec2 allocate-address --domain vpc \
  --tag-specifications "ResourceType=elastic-ip,Tags=[{Key=Name,Value=$NOMBRE}]" \
  --query AllocationId --output text)
aws ec2 associate-address --instance-id "$instancia" --allocation-id "$asignacion" >/dev/null
ip=$(aws ec2 describe-addresses --allocation-ids "$asignacion" --query 'Addresses[0].PublicIp' --output text)

cat <<EOF
Instancia $instancia lista en $ip ($TIPO, $REGION).

Siguientes pasos (infra/README.md · Primera puesta en marcha):
  1. DNS: registros A de <dominio> y staging.<dominio> hacia $ip.
  2. Esperar unos minutos a que termine cloud-init: ssh cedis@$ip cloud-init status --wait
  3. Copiar los archivos de entorno y levantar Caddy.
EOF
