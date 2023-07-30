from lib import csDetector, logger
import sys

if __name__ == "__main__":
    logger = logger.Logger()
    inputData = sys.argv[1:]
    tool = csDetector.CsDetector()
    formattedResult, result, config = tool.executeTool(inputData)

    print(result)
