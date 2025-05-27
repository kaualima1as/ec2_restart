import time

import boto3


def handler(event, context):
    instance_id = event.get("instance_id") if event else None
    if not instance_id:
        print("Instance ID not provided")
        return

    ec2 = boto3.client("ec2")
    ssm = boto3.client("ssm")

    try:
        response_ec2 = ec2.describe_instances(InstanceIds=[instance_id])
        state = response_ec2["Reservations"][0]["Instances"][0]["State"]["Name"]

        if state == "running":
            response_ssm = ssm.send_command(
                InstanceIds=[instance_id],
                DocumentName="AWS-RunShellScript",
                Parameters={
                    "commands": [
                        "mkdir app/test_directory/test",
                        "echo 'This is a test file.' > test_directory/test_file.txt",
                        "ls -l test_directory",
                    ]
                },
            )

            command_id = response_ssm["Command"]["CommandId"]

            time.sleep(120)  # Wait for the command to be processed

            output = ssm.get_command_invocation(
                CommandId=command_id, InstanceId=instance_id
            )
            # response_ec2 = ec2.reboot_instances(InstanceIds=[instance_id])
            return {
                "body": f"Reboot initiated for instance {instance_id}. Response: {response_ec2}",
                "ssm": f"SSM output: {output}",
                "statusCode": 200,
            }
        elif state == "stopped":
            return {
                "body": f"Instance {instance_id} is stopped.",
                "statusCode": 200,
            }
        else:
            return {
                "body": f"Instance {instance_id} is in '{state}' state. No action taken.",
                "statusCode": 200,
            }
    except Exception as e:
        return {"body": f"An error occurred: {str(e)}", "statusCode": 500}
