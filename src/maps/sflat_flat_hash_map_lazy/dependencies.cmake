# every table starts with the golden-ratio multiplier and takes a seed only
# when its keys pile up
target_compile_definitions(${EXECUTABLE_NAME} PRIVATE SFLAT_LAZY_SEED=1)
