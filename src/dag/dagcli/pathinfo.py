import dag


@dag.cmd
def reset_pathinfo():
	from dag import pathmanager_dagmod
	from dag import config_module
	from dag.dagcli import bash_dagapp
	from dag.dagcli import base_cli_dagmod
	from dag import apps

	with dag.file.open(dag.PATHINFO_PATH, "w") as file:
		file.write(pathmanager_dagmod.__file__ + "\n")
		file.write(config_module.__file__ + "\n")
		file.write(bash_dagapp.__file__ + "\n")
		file.write(base_cli_dagmod.__file__ + "\n")
		file.write(str(dag.Path(apps.__file__).parent) + "\n")