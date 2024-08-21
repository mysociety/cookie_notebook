import shutil
import os
import subprocess
from pathlib import Path

template_dir = r"{{ cookiecutter._template }}"
if any(x in template_dir for x in ["https:", "gh:"]):
    repo_name = template_dir.split("/")[-1]
    template_dir = Path.home() / ".cookiecutters" / repo_name
else:
    template_dir = Path(template_dir)

template_repo = "https://github.com/mysociety/template_data_repo"
template_branch = "main"

helper_repo = "https://github.com/mysociety/data_common"
helper_branch = "main"


# this was all a submodule in the template, now it stands alone. Need to copy across the git info.
# this is made conditional because in a templating test it won't be set up this way, but also that's fine. 
if os.environ.get("UPDATE_TO_LATEST", "true").lower() == "true":
    Path(".git").unlink()
    real_git_folder = Path(template_dir) / ".git" / "modules" / ("{" + "{ cookiecutter.repo_name }" + "}")
    shutil.copytree(real_git_folder, ".git")
    git_config = Path(".git", "config")
    notebook_git_config = Path(".git","modules", "src", "data_common", "config")

    # remove reference to the work tree above
    with open(git_config, "r") as f:
        lines = f.readlines()
    with open(git_config, "w") as f:
        for line in lines:
            if "cookiecutter.repo_name" not in line:
                f.write(line)

    # remove reference to the work tree above
    with open(notebook_git_config, "r") as f:
        lines = f.readlines()
    with open(notebook_git_config, "w") as f:
        for line in lines:
            if "cookiecutter.repo_name" not in line:
                f.write(line)
            else:
                f.write("	worktree = ../../../../src/data_common\n")

    # adjust the git directory for the notebook helper
    with open(Path("src","data_common",".git"), "w") as file:
        file.write("gitdir: ../../.git/modules/src/data_common")

#copy example env to env
shutil.copyfile(Path(".env-example"),
                Path(".env"))

# when doing this on windows, sometimes clones bad line endings. 
# This fixes the bash file docker uses. 
# replacement strings
WINDOWS_LINE_ENDING = b'\r\n'
UNIX_LINE_ENDING = b'\n'

# relative or absolute file path, e.g.:
file_path = Path("src","data_common", "bin", "packages_setup.bash")

with open(file_path, 'rb') as open_file:
    content = open_file.read()
    
content = content.replace(WINDOWS_LINE_ENDING, UNIX_LINE_ENDING)

with open(file_path, 'wb') as open_file:
    open_file.write(content)

# Lock the upstream docker image source at point of departure from template

data_common_tag = subprocess.check_output("git submodule status src/data_common", shell=True).strip()
data_common_tag = data_common_tag.replace(b"+", b"")
data_common_tag = data_common_tag[:7]

data_common_tag = b"data_common:sha-" + data_common_tag

for d in ["Dockerfile"]:

    with open(d, 'rb') as open_file:
        content = open_file.read()
        
    content = content.replace(b"data_common:latest", data_common_tag)

    with open(d, 'wb') as open_file:
        open_file.write(content)

# remove templates we haven't already copied into the higher level
bad_workflows = [Path(".github", "workflows", "template_meta_test.yaml")]

for w in bad_workflows:
    w.unlink()

if os.environ.get("UPDATE_TO_LATEST", "true").lower() == "true":

    # remove, we don't want this project to have a default origin of the template library
    os.system(f'git remote rm origin')

    # package all up in a little box
    os.system("git add --all")
    os.system('git commit -m "Post-templating commit"')
