from lib import csDetector, logger
import sys

if __name__ == "__main__":
    logger = logger.Logger()
    logger.log("info","Started application")
    inputData = sys.argv[1:]
    tool = csDetector()
    formattedResults, results, config = tool.executeTool(inputData)
    print(results)
    print(formattedResults)
