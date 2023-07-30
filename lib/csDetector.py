from lib import csFactory 

# since the interface of the execution is only command line input, we want something to adapt our web service
# we will have an adapter class that will extend csDetector and parses the local input

class CsDetector:

    def executeTool(self, argv):
        cs_builder = csFactory.CSFactory(argv)
        return cs_builder.getCommunitySmells()
