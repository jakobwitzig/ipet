from distutils.core import setup

setup(
    name='Ipet--Interactive Python Evaluation Tools',
    version='0.1dev',
    packages=['ipet',],
    license='Creative Commons Attribution-Noncommercial-Share Alike license',
    long_description="""
        Ipet contains python modules for collecting and evaluating
        MIP benchmark data in raw format. It comes with a graphical
        user interface to collect, view, and transform benchmark
        data. It can also be used as a library for interactive use
        from a command-line interpreter aka python or ipython.
        """
)