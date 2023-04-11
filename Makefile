build: CHANGES README MANIFEST.in setup.py
	#rm -rf /tmp/RuSocSci
	#mkdir /tmp/RuSocSci
	#cp -a * /tmp/RuSocSci
	#cd /tmp/RuSocSci; python3 setup.py sdist --formats=zip
	#cd /tmp/RuSocSci; python3 setup.py bdist_wheel
	python3 setup.py bdist_wheel
	
upload:
	#cd /tmp/RuSocSci; python3 setup.py sdist --formats=zip upload
	#cd /tmp/RuSocSci; twine upload --repository-url https://test.pypi.org/legacy/ dist/*
	#cd /tmp/RuSocSci; twine upload dist/*
	twine upload dist/*

epydoc: 
	epydoc rusocsci
	rm -f doc.zip; cd html; zip ../doc.zip *; cd ..
	firefox 'https://pypi.python.org/pypi?:action=pkg_edit&name=RuSocSci'
doc:
	rm -rf /tmp/RuSocSci
	mkdir /tmp/RuSocSci
	cp -a * /tmp/RuSocSci
	cd /tmp/RuSocSci; sphinx-apidoc -F -o html rusocsci
	cd /tmp/RuSocSci/html; PYTHONPATH=~/Documents/Python/RuSocSci make html
	cd /tmp/RuSocSci/html/_build/html; zip -r doc.zip *
	cp /tmp/RuSocSci/html/_build/html/doc.zip .
	#firefox 'https://pypi.python.org/pypi?:action=pkg_edit&name=RuSocSci'

clean:
	rm -rf RuSocSci.egg-info dist build
