# <<[.custom.project.name]>>

<<[.custom.project.description]>>

# Author(s)

<<[range $i, $auth := .custom.project.authors ]>>
<<[$i]>> [<<[$auth.name]>>](https://github.com/<<[$auth.id]>>)
<<[ end ]>>
