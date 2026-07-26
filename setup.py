from setuptools import setup, find_packages

setup(
    name="cqrlib",
    version="0.1.0",
    description="CQR Library - Quantitative Research Library for financial machine learning",
    author="Quantitative Research Team",
    license="MIT",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.17.3",
        "pandas>=1.0.3",
        "scipy>=1.3.1",
        "scikit-learn>=0.23.1",
        "matplotlib>=3.1.1",
        "statsmodels>=0.11.1",
        "numba>=0.49.1",
        "cvxpy>=1.0.0",
    ],
    python_requires=">=3.8",
)
