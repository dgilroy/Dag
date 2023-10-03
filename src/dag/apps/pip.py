from pip._internal.commands import commands_dict
import pkg_resources

import dag
from dag import r_

# Retrieve a list of all installed packages
installed_packages = pkg_resources.working_set

# Extract the package names from the working set
installed_package_names = [package.key for package in installed_packages]


pip = dag.app("pip")

packages = pip.collection.GET("https://hugovk.github.io/top-pypi-packages/top-pypi-packages-30-days.min.json", r_.rows)
packages.resources("package").label("project")


installed_packages = pip.collection("installed_package", value = installed_package_names)
installed_packages.resources("package").label("label")


install = packages.op("install").RAW.RUN("pip install " + dag.args.package.project)


show = installed_packages.op("show").RUN("pip show " + dag.args.package.label)


help = pip.DEFAULT.cmd("help").RUN("pip --help")


@pip.cmd(*[k for k in commands_dict if k not in pip.dagcmds.names()])
def pipcmds(*args):
	return dag.cli.run(" ".join(("pip", dag.ctx.active_dagcmd.name) + args))
