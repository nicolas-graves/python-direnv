(use-modules (guix packages)
             (guix download)
             (guix git-download)
             ((guix licenses) #:prefix license:)
             (gnu packages check)
             (gnu packages python)
             (gnu packages python-build)
             (gnu packages python-xyz)
             (guix build-system pyproject)
             (guix build-system python))

(define %srcdir
  (dirname (current-filename)))

(packages->manifest
 (list
  python
  python-dotenv
  python-ipython
  python-pypa-build
  python-pytest
  python-twine
  (package
   (name "python-direnv")
   (version "0.0.0")
    (source
     (local-file "." "python-direnv"
                 #:recursive? #t
                 #:select? (git-predicate %srcdir)))
    (build-system pyproject-build-system)
    (arguments '(#:tests? #f))
    (native-inputs (list python-hatchling))
    (propagated-inputs (list python-ipython))
    (home-page "")
    (synopsis "")
    (description "")
    (license license:bsd-3))))
