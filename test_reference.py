"""Unit tests for newly authored reference implementation; no published-results assertions."""
import math,unittest
import numpy as np
from reference_controller.aac_hocbf import (AACController,Config,ControllerState,
     TargetMessage,uncertainty_radius,travel_time_1d,saturate)


class ReferenceControllerTests(unittest.TestCase):
    def test_uncertainty_radius_monotonic(self):
        ages=np.linspace(0,11,111)
        radii=[uncertainty_radius(float(x)) for x in ages]
        self.assertTrue(all(a<=b for a,b in zip(radii,radii[1:])))
        with self.assertRaises(ValueError):uncertainty_radius(11.1)
    def test_speed_saturation(self):
        v=saturate(np.array([9.,12.]),3)
        self.assertAlmostEqual(np.linalg.norm(v),3)
    def test_1d_time(self):
        self.assertGreater(travel_time_1d(8,0,3,1.5),0)
        self.assertEqual(travel_time_1d(0,0,3,1.5),0)
        self.assertTrue(math.isinf(travel_time_1d(3,0,-1,1.5)))
    def test_release_and_state_update(self):
        c=Config();controller=AACController(c)
        s=ControllerState(np.array([[-8,0],[8,0]]),np.zeros((2,2)))
        msgs=[TargetMessage(np.array([5.,0]),np.zeros(2),0),
              TargetMessage(np.array([-5.,0]),np.zeros(2),0)]
        ns,diag=controller.step(0.,s,msgs)
        self.assertTrue(diag['released'])
        self.assertEqual(ns.phase,'terminal')
        self.assertTrue(np.all(np.linalg.norm(ns.velocities,axis=1)<=c.vmax+1e-9))
    def test_filter_respects_acceleration(self):
        c=Config();controller=AACController(c)
        s=ControllerState(np.array([[-4.,0],[4.,0]]),np.zeros((2,2)))
        u=np.array([[1.,0],[-1.,0]])
        safe,diag=controller.filter_control(s,u)
        self.assertTrue(diag['success'],str(diag))
        self.assertTrue(np.all(np.linalg.norm(safe,axis=1)<=c.umax+1e-6))

if __name__=='__main__':unittest.main()
