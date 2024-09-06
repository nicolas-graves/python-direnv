(use-modules (git)
             (guix packages)
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

(define %commit
  (let ((repository (repository-open %srcdir)))
    (oid->string (object-id (revparse-single repository "master")))))

(packages->manifest
 (list
  python
  python-ipython
  python-pytest
  (package/inherit python-direnv
   (version (git-version "0.2.2" "0" %commit))
    (source
     (local-file "." "python-direnv"
                 #:recursive? #t
                 #:select? (git-predicate %srcdir)))
    (build-system pyproject-build-system)
    (arguments '(#:tests? #f))
    (native-inputs (list python-flit-core)))))
