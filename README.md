# 🧹 Automação de Limpeza e Reinicialização de EC2 com AWS Lambda + SSM

Este projeto tem como objetivo automatizar a **limpeza de recursos desnecessários e a reinicialização periódica** de instâncias EC2, garantindo desempenho consistente e liberação de espaço em disco — tudo de forma **automática e sem intervenção manual**.

---

## 📌 Visão Geral

| Etapa                         | Descrição                                                                 |
|------------------------------|---------------------------------------------------------------------------|
| ✅ Passos para Implementação  | Guia prático para configurar a automação                                 |
| 🧠 Código                     | Função Lambda em Python com `boto3`                                       |
| 🧹 Comandos de Limpeza        | Scripts executados via SSM nas instâncias EC2                            |
| 📁 Repositório                | Este projeto contém todo o código necessário                             |

---

## 🎯 Objetivo

Automatizar tarefas de manutenção em instâncias EC2, como:
- Liberação de espaço em disco.
- Eliminação de arquivos temporários.
- Remoção de imagens e volumes Docker não utilizados.
- Reinicialização das instâncias após a limpeza.

---

## ⚙️ Arquitetura Utilizada

- **Amazon EC2:** Máquinas virtuais que serão limpas.
- **AWS Systems Manager (SSM):** Execução remota de comandos com segurança.
- **AWS Lambda:** Função que orquestra o processo de limpeza e reboot.
- **Amazon EventBridge:** Agendamento da execução da Lambda.
- **AWS IAM:** Controle de permissões entre os serviços.

---

## 🧩 Passos para Implementação

### 1. ✅ Preparar a EC2
- Verifique se o **SSM Agent** está instalado e em execução (a maioria das AMIs já vem com ele).
- Anexe à EC2 uma **IAM Role** com a política `AmazonSSMManagedInstanceCore`.

### 2. 🧠 Criar a Função Lambda
- Use o código Python disponível em [`lambda_function.py`](./lambda_function.py).
- A função recebe o ID da instância como entrada e executa os comandos definidos.

**Permissões mínimas (IAM Role da Lambda):**
- `AmazonSSMFullAccess`
- `ec2:DescribeInstances`
- `ec2:RebootInstances`

### 3. ⏱️ Agendar via Amazon EventBridge
- Crie uma regra de cron (ex: diariamente às 23h) que acione a função Lambda com o ID da instância como parâmetro.

---

## 🧼 Comandos de Limpeza Utilizados

```bash
# Limpeza de pacotes e arquivos temporários
sudo apt-get autoremove -y
sudo apt-get autoclean -y
sudo apt-get clean
sudo rm -rf /tmp/*
sudo rm -rf /var/tmp/*

# Limpeza de recursos Docker não utilizados
docker system prune -f > /tmp/clean_activity.log 2>&1
docker image prune -a -f >> /tmp/clean_activity.log 2>&1
docker volume prune -f >> /tmp/clean_activity.log 2>&1

# Coleta de lixo para sistemas baseados em Nix
nix-collect-garbage -d >> /tmp/clean_activity.log 2>&1

# Redução de logs antigos
sudo journalctl --vacuum-time=7d

# (Opcional) Limpeza de cache do usuário
rm -rf ~/.cache/*

# Exibir log da atividade
cat /tmp/clean_activity.log
