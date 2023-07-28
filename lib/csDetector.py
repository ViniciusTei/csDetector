from lib import csBuilder 

# since the interface of the execution is only command line input, we want something to adapt our web service
# we will have an adapter class that will extend csDetector and parses the local input

class CsDetector:

    def executeTool(self, argv):
        cs_builder = csBuilder.CSBuilder(argv)
        results = cs_builder.getCommunitySmells()
        return results
