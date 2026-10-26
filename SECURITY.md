# Security policy

This is a static browser-side application without a project backend. Please report security issues through GitHub's private vulnerability reporting feature if it is enabled for the repository; otherwise contact the maintainers through a channel listed in the repository profile.

Do not submit proprietary or sensitive model files in a public issue. Import only files you trust. The app parses local binary data and generates downloadable outputs; parser fixes should validate lengths, offsets, counts and file-size bounds before reading or allocating data.
