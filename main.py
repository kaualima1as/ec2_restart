import boto3


def handler(event, context):
    instance_id = event.get("instance_id") if event else None
    if not instance_id:
        print("Instance ID not provided")
        return

    ec2 = boto3.client("ec2")
    try:
        response = ec2.reboot_instances(InstanceIds=[instance_id])
        print(f"Reboot initiated for instance {instance_id}. Response: {response}")
    except Exception as e:
        print(f"Error rebooting instance: {e}")
