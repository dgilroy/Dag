import dag
from dag.lib import ctxmanager, dot


class DagCtx(ctxmanager.Context):
	pass




instance_ctx = DagCtx()
#instance_ctx = ctxmanager.Context()
instance_ctx.directives = dot.DotDict()
