import os


def clone_repo(url):
    os.system("git clone {}".format(url))
    return url.split("/")[-1]

def download_repo(url):
    os.system("wget {}".format(url))
    return url.split("/")[-3], url.split("/")[-1][:-4]

def unzip(repo_name, version):
    os.system("mkdir {}".format(repo_name))
    os.system("unzip {} -d {}".format(version+".zip", repo_name))
    os.system("rm -r {}".format(version+".zip"))


### CHANGE THIS
url = 'https://github.com/apache/kafka/archive/refs/heads/trunk.zip'

repo_name, version = download_repo(url)
unzip(repo_name, version)

### CHANGE THIS
file_name  = './refs/kafka-trunk/shell/src/main/java/org/apache/kafka/shell/LsCommandHandler.java'
# file_name = "./refs/kafka-trunk/tools/src/main/java/org/apache/kafka/tools/VerifiableConsumer.java"

# LR = LogRetriver(file_name, "./")
# a, b, = LR.extract_log_messages()
