# Data Minimization on Permanent Case Closure

To honor whistleblower confidentiality and prevent perpetual retention of sensitive evidence once an investigation concludes, transitioning a report to `PERMANENTLY_CLOSED` immediately overwrites the report description with a redaction marker, unlinks any uploaded evidence files from local disk storage, and freezes the dead-drop communication thread. This trades off historical evidence forensics in favor of strict data minimization and immunity against retrospective data leaks.
