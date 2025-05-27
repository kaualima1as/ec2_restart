import time

import boto3


def handler(event, context):
    instance_id = event.get("instance_id") if event else None
    if not instance_id:
        return {"body": "Instance ID not provided", "statusCode": 400}

    ec2 = boto3.client("ec2")
    ssm = boto3.client("ssm")

    try:
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
                "cd /home/ubuntu",
                "sudo apt-get autoremove -y",
                "sudo apt-get autoclean -y",
                "sudo apt-get clean",
                "docker system prune -f > /tmp/clean_activity.log 2>&1",
                "echo -e \n\n\n >> /tmp/clean_activity.log",
                "docker image prune -a -f >> /tmp/clean_activity.log 2>&1",
                "echo -e \n\n\n >> /tmp/clean_activity.log",
                "docker volume prune -f >> /tmp/clean_activity.log 2>&1",
                "echo -e \n\n\n >> /tmp/clean_activity.log",
                "echo --- Cleaning Nix ---",
                "nix-collect-garbage -d >> /tmp/clean_activity.log 2>&1",
                "echo --- Cleaning temp and logs ---",
                "sudo rm -rf /tmp/*",
                "sudo rm -rf /var/tmp/*",
                "sudo journalctl --vacuum-time=7d"
                "echo --- Cleaning pip and cache ---"
                "rm -rf ~/.cache/*",
                "cat /tmp/clean_activity.log",
            ]

            response_ssm = ssm.send_command(
                InstanceIds=[instance_id],
                DocumentName="AWS-RunShellScript",
                Parameters={"commands": commands},
            )

            command_id = response_ssm["Command"]["CommandId"]

            ssm_output = None
            ssm_status = "Pending"
            max_attempts = 24
            attempts = 0

            while (
                ssm_status in ["Pending", "InProgress", "Delayed"]
                and attempts < max_attempts
            ):
                attempts += 1
                time.sleep(5)
                try:
                    ssm_output = ssm.get_command_invocation(
                        CommandId=command_id, InstanceId=instance_id
                    )
                    ssm_status = ssm_output["Status"]
                except ssm.exceptions.InvocationDoesNotExist:
                    ssm_status = "Pending"
                    if attempts >= max_attempts:
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
                return {
                    "body": error_message,
                    "ssm_output": str(
                        ssm_output
                    ),  # Incluir o output completo para debug
                    "statusCode": 500,
                }

            print("-- START OF OUTPUT --")
            if ssm_output and ssm_output.get("StandardOutputContent"):
                print(ssm_output["StandardOutputContent"])
            else:
                print("No output from SSM command.")
            print("-- END OF OUTPUT --")

            final_message_body = f"Instance {instance_id} processed. SSM commands successful. Reboot was NOT initiated (code commented out)."

            ec2.reboot_instances(InstanceIds=[instance_id])

            print(f"Instance {instance_id} rebooted successfully.")

            return {
                "body": final_message_body,
                "ssm_output_details": str(ssm_output),
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
