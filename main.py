import time

import boto3


def handler(event, context):
    instance_id = event.get("instance_id") if event else None
    if not instance_id:
        print("Instance ID not provided")
        return {"body": "Instance ID not provided", "statusCode": 400}

    ec2 = boto3.client("ec2")
    ssm = boto3.client("ssm")

    try:
        # Verifica o estado da instância primeiro
        instance_info = ec2.describe_instances(InstanceIds=[instance_id])
        if (
            not instance_info["Reservations"]
            or not instance_info["Reservations"][0]["Instances"]
        ):
            print(f"Instance {instance_id} not found.")
            return {"body": f"Instance {instance_id} not found.", "statusCode": 404}
        state = instance_info["Reservations"][0]["Instances"][0]["State"]["Name"]

        if state == "running":
            commands = [
                "mkdir -p /home/ubuntu/app/test_directory/test",
                "echo 'This is a test file.' > /home/ubuntu/app/test_directory/test/test_file.txt",
                "ls -l app/test_directory/test",
            ]

            print(f"Sending commands to instance {instance_id}: {commands}")
            response_ssm = ssm.send_command(
                InstanceIds=[instance_id],
                DocumentName="AWS-RunShellScript",
                Parameters={"commands": commands},
            )

            command_id = response_ssm["Command"]["CommandId"]
            print(f"SSM Command ID: {command_id} sent to instance {instance_id}")

            ssm_output = None
            ssm_status = "Pending"
            max_attempts = 24
            attempts = 0

            while (
                ssm_status in ["Pending", "InProgress", "Delayed"]
                and attempts < max_attempts
            ):
                attempts += 1
                time.sleep(5)  # Espera 5 segundos entre as tentativas
                try:
                    ssm_output = ssm.get_command_invocation(
                        CommandId=command_id, InstanceId=instance_id
                    )
                    ssm_status = ssm_output["Status"]
                    print(
                        f"SSM Command status: {ssm_status} (Attempt {attempts}/{max_attempts})"
                    )
                except ssm.exceptions.InvocationDoesNotExist:
                    # Pode acontecer se o comando ainda não foi registrado completamente
                    print(
                        f"SSM Invocation for Command ID {command_id} not found yet. Retrying... (Attempt {attempts}/{max_attempts})"
                    )
                    ssm_status = "Pending"  # Continua tentando
                    if (
                        attempts >= max_attempts
                    ):  # Evita loop infinito se nunca aparecer
                        print("SSM command invocation never appeared.")
                        return {
                            "body": f"SSM command {command_id} invocation did not appear after {attempts * 5} seconds.",
                            "statusCode": 500,
                        }
                    continue  # Pula para a próxima tentativa

            if ssm_status != "Success":
                error_message = f"SSM command {command_id} failed or timed out with status: {ssm_status}."
                if ssm_output and ssm_output.get("StandardErrorContent"):
                    error_message += (
                        f" Error details: {ssm_output.get('StandardErrorContent')}"
                    )
                print(error_message)
                return {
                    "body": error_message,
                    "ssm_output": str(
                        ssm_output
                    ),  # Incluir o output completo para debug
                    "statusCode": 500,
                }

            final_message_body = f"Instance {instance_id} processed. SSM commands successful. Reboot was NOT initiated (code commented out)."

            return {
                "body": final_message_body,
                "ssm_output_details": str(
                    ssm_output
                ),  # Retorna o output completo do SSM
                "statusCode": 200,
            }
        elif state == "stopped":
            return {
                "body": f"Instance {instance_id} is stopped. No action taken.",
                "statusCode": 200,
            }
        else:
            return {
                "body": f"Instance {instance_id} is in '{state}' state. No action taken.",
                "statusCode": 200,
            }
    except Exception as e:
        return {"body": f"An error occurred: {str(e)}", "statusCode": 500}
