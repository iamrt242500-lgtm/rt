# Top-level Makefile

.PHONY: core core-example clean core-make core-make-example

CORE_DIR := pqc_core
BUILD_DIR := $(CORE_DIR)/build

core:
	@mkdir -p $(BUILD_DIR)
	@cd $(BUILD_DIR) && cmake .. && $(MAKE)

core-example: core
	@cd $(BUILD_DIR) && $(MAKE) example

clean:
	@rm -rf $(BUILD_DIR)

# Fallback without CMake
core-make:
	@$(MAKE) -C $(CORE_DIR)

core-make-example: core-make
	@$(MAKE) -C $(CORE_DIR) run
