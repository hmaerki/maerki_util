# -*- coding: utf-8 -*-
"""
  Configurationfile for scanning.
  Doubleclick this file to scan using a given configuration.
"""
import os
import pyscan.utils as utils
import pyscan.algorithms_pil_enhance as algorithms_pil_enhance

class Vorlage:
  """
    Defines how to scan and postprocess.
  """
  def getDpi(self):
    return 300, utils.WIA_INTENT_IMAGE_TYPE_GRAYSCALE

  def postProcess(self, strFilenameBmp, strFilenameFinal):
    """
      The scanned image is ready under strFilenameBmp.
      Postprocess the image now.
    """
    # algorithms_pil_enhance.horizontalMirrorBMP(strFilenameBmp)
    algorithms_pil_enhance.rotateBMP(strFilenameBmp)

    # algorithms_pil_enhance.enhance5(strFilenameBmp, strFilenameBmp.replace('.bmp', '.png'), bVerkleinern=False, iRasterEntfernen=None)
    # algorithms_pil_enhance.enhance5(strFilenameBmp, strFilenameBmp.replace('.bmp', '.png'), bVerkleinern=False, iRasterEntfernen=5, bHelligkeitskorrektur=True)
    # Laser
    iDpi, dummy = self.getDpi()
    algorithms_pil_enhance.enhance6(strFilenameBmp, strFilenameFinal, bVerkleinern=False, iRasterEntfernen=3, iAlphaBW=120, iBlackWhite=220, iDpi=iDpi)
    # os.remove(strFilenameBmp)

if __name__ == "__main__":
  utils.scan(Vorlage())
  utils.openFolder()

