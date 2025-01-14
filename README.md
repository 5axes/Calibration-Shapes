# Calibration Shapes Reborn
A somewhat scaled-back continuation of [Calibration Shapes by 5@xes](https://github.com/5axes/Calibration-Shapes/).

This plugin adds a menu to create some simple shapes to the scene (cube, sphere, cylinder, tube) and calibration sample parts.

This has removed several features available in the original version to be easier for me to maintain:
- **Now requires Cura 5.0 or higher.** This has allowed me to remove legacy code.
- Test towers are gone. [AutoTowers Generator](https://github.com/kartchnb/AutoTowersGenerator) does a far better job than I ever could.
- Any other calibration prints which relied on post-processing scripts have also been removed.
- I can't make any promises about the few translations that were in the original still working.

The default size for the simple shapes is 20 mm, but can be modified via the *Set default size* menu option.

---
### If something isn't working, I want to know! Just create something in the [issues](https://github.com/Slashee-the-Cow/CalibrationShapesReborn/issues) page.
### If you want to say hi, I'd love to hear it! [Discussions](https://github.com/Slashee-the-Cow/CalibrationShapesReborn/discussions) is the place for you.

---

Based on [Calibration Shapes by 5@xes](https://github.com/5axes/Calibration-Shapes/) which itself was based on [Cura-SimpleShapes by fieldOfView](https://github.com/fieldOfView/Cura-SimpleShapes).  
Uses the [Trimesh](https://github.com/mikedh/trimesh) library to create [simple shapes](https://github.com/mikedh/trimesh/blob/master/trimesh/creation.py) and to load STL files.