import boto3


def handler(event, context):
    instance_id = event.get("instance_id") if event else None
    if not instance_id:
        print("Instance ID not provided")
        return

    ec2 = boto3.client("ec2")
    try:
        response = ec2.reboot_instances(InstanceIds=[instance_id])
        return {
            "body": f"Reboot initiated for instance {instance_id}. Response: {response}",
            "statusCode": 200,
        }
    except Exception as e:
        return {"body": f"An error occurred: {str(e)}", "statusCode": 500}
