
"""
  Configurationfile for scanning.
  Doubleclick this file to scan using a given configuration.
"""
import pyscan.utils as utils
import pyscan.algorithms_pil_enhance as algorithms_pil_enhance
import os

class Vorlage:
  """
    Defines how to scan and postprocess.
  """
  def getDpi(self):
    return 300, utils.WIA_INTENT_IMAGE_TYPE_COLOR

  def postProcess(self, strFilenameBmp, strFilenameFinal):
    """
      The scanned image is ready under strFilenameBmp.
      Postprocess the image now.
    """
    # algorithms_pil_enhance.horizontalMirrorBMP(strFilenameBmp)
    algorithms_pil_enhance.rotateBMP(strFilenameBmp)

    # for iQuality in (5, 10, 50, 70, 100):
    iQuality = 100
    iDpi, dummy = self.getDpi()
    # strFilenameFinal = strFilenameFinal.replace('.png', '.jpg')
    algorithms_pil_enhance.saveas(strFilenameBmp, strFilenameFinal, iQuality=iQuality, iDpi=iDpi)

    # os.remove(strFilenameBmp)

if __name__ == "__main__":
  utils.scan(Vorlage())
  utils.openFolder()

