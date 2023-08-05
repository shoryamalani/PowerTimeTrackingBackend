# import constants
# import subprocess
# title = "Fixate"
# subtitle = "New Message"
# body = "You have a new message from a Fixate user."

# curl_command = [
#     ["curl -v","--cert", constants.AUTH_FILE_PATH,],
#     ["--cert-type", "DER",],
#     ["--key", constants.CERT_FILE_PATH],
#     ["--key-type", "PEM"],
#     ["--header", '"apns-topic: com.shoryamalani.fixate"',],
#     ["--header", '"apns-push-type: alert"',],
#     ["--header", '"apns-priority: 5"'],
#     ["--header", '"apns-expiration: 0"'],
#     [ "--data", '\'{"aps":{"alert":{"title":"'+title+'","subtitle":"'+subtitle+'","body":"'+body+'"}}}\'',],
#     ["--http2", "https://api.development.push.apple.com:443/3/device/" + device_id]
# ]


# final_command = ""
# for line in curl_command:
#     final_command += " ".join(line) + " \\\n"
# print(final_command)
# subprocess.run(final_command, shell=True)