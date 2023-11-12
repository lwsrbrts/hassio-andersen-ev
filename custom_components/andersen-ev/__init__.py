DOMAIN = "andersen"

def setup(hass, config):
    hass.states.set("andersen.world", "Lewis")

    # Return boolean to indicate that initialization was successful.
    return True