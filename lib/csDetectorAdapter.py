from lib.csDetector import CsDetector
import logging

# this is the adapter class. we can use it to call the adapter from different sources of input
# by inheriting csDetector, we override the method with bad specified interface with a better
# one that will call the superclass method after parsing the given input

class CsDetectorAdapter(CsDetector):
    def __init__(self):
        super().__init__()

    def executeTool(self, gitRepository, gitPAT, startingDate="null", sentiFolder="./senti", outputFolder="./out"):

        if(startingDate == "null"):
            arguments = ["-p", gitPAT, "-r", gitRepository, "-s", sentiFolder, "-o", outputFolder]
            logging.info(f"Excuting tool with: {arguments}")
            print(f"Excuting tool with: {arguments}")
            # in this branch we execute the tool normally because no date was provided
        else:
            arguments = ["-p", gitPAT, "-r", gitRepository, "-s", sentiFolder, "-o", outputFolder, '-sd', startingDate]
            logging.info(f"Excuting tool with: {arguments}")
            print(f"Excuting tool with: {arguments}")
            # if a date is specified we have to execute with one more parameter
        
        return super().executeTool(arguments)


if __name__ == "__main__":

    tool = CsDetectorAdapter()
    formattedResult, result, _ = tool.executeTool("https://github.com/tensorflow/ranking",
                                               "")
    print(result)
    print(formattedResult)
