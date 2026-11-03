import inspect

from hardware import VexHardware
from sim_hardware import SimHardware


def public_methods(cls):
    return dict((name, inspect.signature(member))
                for name, member in inspect.getmembers(cls, inspect.isfunction)
                if not name.startswith("_"))


def test_hardware_module_imports_without_vex():
    # importing hardware above already proved it; check the guard is why
    import hardware
    assert not hasattr(hardware, "Brain")


def test_sim_has_every_hardware_method_with_the_same_arguments():
    vex = public_methods(VexHardware)
    sim = public_methods(SimHardware)
    for name, signature in vex.items():
        assert name in sim, "SimHardware is missing %s" % name
        assert list(signature.parameters) == list(sim[name].parameters), name


def test_sim_has_no_extra_public_methods():
    # robot code must not come to rely on something only the simulator has
    extra = set(public_methods(SimHardware)) - set(public_methods(VexHardware))
    assert not extra
