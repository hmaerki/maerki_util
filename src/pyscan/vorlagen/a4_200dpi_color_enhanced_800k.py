# -*- coding: utf-8 -*-
import os
import pyscan.utils as utils
import pyscan.algorithms_pil_enhance as algorithms_pil_enhance

class Vorlage:
  """
    Defines how to scan and postprocess.
  """
  def getDpi(self):
    return 200, utils.WIA_INTENT_IMAGE_TYPE_COLOR

  def postProcess(self, strFilenameBmp, strFilenameFinal):
    """
      The scanned image is ready under strFilenameBmp.
      Postprocess the image now.
    """
    algorithms_pil_enhance.rotateBMP(strFilenameBmp)

    # strFilenameFinal = strFilenameFinal.replace('.png', '.jpg')
    iDpi, dummy = self.getDpi()
    algorithms_pil_enhance.enhanceColor(strFilenameBmp, strFilenameFinal, iBlack=70, iWhite=220, iDpi=iDpi)

if __name__ == "__main__":
  utils.scan(Vorlage())
  utils.openFolder()