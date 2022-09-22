import dag
from dag import this


from dag.lib.mathtools import Convert


@dag.mod("webb", baseurl = "https://api.jwst-hub.com/", help = "James Web Tracker Info", default_cmd = this.track, launch = "http://www.nhl.com", response_parser = dag.JSON)
class JamesWebb(dag.DagMod):

	@dag.cmd(value = dag.nab.get("track"), display = this._display_tracker, message = "James Webb Tracker Info")
	def track(self):
		"""Track deployment status of JWST"""
		return

	
	def _display_tracker(self, response, formatter):
		formatter.col(suffix = ": ").col(style = "b")

		formatter = dag.img.from_url(response.deploymentImgURL).to_formatter(formatter, maxheight = 20)

		formatter.add_row("Distance from earth", f"{Convert.km_to_miles(response.distanceEarthKm)} miles")
		formatter.add_row("Distance to L2", f"{Convert.km_to_miles(response.distanceL2Km)} miles")
		formatter.add_row("Distance % Complete", f"{response.percentageCompleted}%")
		formatter.add_row("Speed", f"{Convert.km_to_miles(response.speedKmS)} mph")

		formatter.add_row("Deployment Step", response.currentDeploymentStep)
		formatter.add_row("Avg Warm Side Temp", f"{Convert.cels_to_kel((response.tempC.tempWarmSide1C + response.tempC.tempWarmSide2C)/2)}˚K")
		formatter.add_row("Avg Cool Side Temp", f"{Convert.cels_to_kel((response.tempC.tempCoolSide1C + response.tempC.tempCoolSide1C)/2)}˚K")