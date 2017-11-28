#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 2017

@author: kostenko

This module includes a few routines useful for modeling polychromatic X-ray CT data

"""
import numpy
import flexSpectrum

def phantom(shape, mode = 'bubble', parameters = [10, 1]):
    """
    Create a phantom image.
    
    Args:
        shape (list): shape of the volume 
        type (str): use 'bubble' or 'pearl'
        parameters (list or float): for the bubble - [outer radius, wall thickness], pearl - radius
    """    
    
    xx = numpy.arange(0, shape[0]) - shape[0] // 2
    yy = numpy.arange(0, shape[1]) - shape[1] // 2
    zz = numpy.arange(0, shape[2]) - shape[2] // 2
                                  
    vol = (xx[:, None, None]**2 + yy[None, :, None]**2 + zz[None, None, :]**2)

    if mode == 'bubble':
        r0 = (parameters[0] - parameters[1])**2
        r1 = (parameters[0])**2
    
        vol = numpy.array(((vol > r0) & (vol < r1)), dtype = 'float32')                 
    elif mode == 'pearl':
        r0 = parameters[0] ** 2
        vol = numpy.array((vol < r0), dtype = 'float32') 

    return vol                

def get_ctf(shape, mode = 'gaussian', parameter = 1):
    """
    Get a CTF (fft2(PSF)) of one of the following types: gaussian, dual_ctf, fresnel
    
    Args:
        shape (list): shape of a projection image
        mode (str): 'gaussian', 'dual_ctf' (phase contrast)
        parameter (list / float): psf parameters. 
                  For gaussian: [detector_pixel, sigma]
                  For dual_ctf: [detector_pixel, energy, src2obj, det2obj, alpha]  
        
    Returns:
        
    """
    if mode == 'gaussian':
        
        # Gaussian CTF:
        pixel = parameter[0]
        sigma = parameter[1]
          
        u = _w_space_(shape, 0, pixel)
        v = _w_space_(shape, 1, pixel)
        
        ctf = numpy.exp(-((u * sigma) ** 2 + (v * sigma) ** 2)/2)
        #ctf = 1 / (2 * numpy.pi * sigma**2) * numpy.exp(-((xx / sigma)**2 + (yy / sigma)**2) / 2)
                   
        return numpy.fft.fftshift(ctf) 
    
    elif mode == 'dual_ctf':
        
        # Dual CTF approximation phase contrast propagator:
        pixelsize = parameter[0]
        energy = parameter[1]
        r1 = parameter[2]
        r2 = parameter[3]
        alpha = parameter[4]
        
        # Effective propagation distance:
        m = (r1 + r2) / r1
        r_eff = r2 / m
        
        # Wavenumber;
        k = energy / (flexSpectrum.phys_const['h_bar_ev'] * flexSpectrum.phys_const['c'])
        
        # Frequency square:
        w2 = _w2_space_(shape, pixelsize)
        
        return -2 * numpy.cos(w2 * r_eff / (2*k)) + 2 * (alpha) * numpy.sin(w2 * r_eff / (2*k))
    
    elif mode == 'fresnel':
        
        # Fresnel propagator for phase contrast simulation:
        pixelsize = parameter[0]
        energy = parameter[1]
        r1 = parameter[2]
        r2 = parameter[3]
        
        # Effective propagation distance:
        m = (r1 + r2) / r1
        r_eff = r2 / m
        
        # Wavenumber;
        k = energy / (flexSpectrum.phys_const['h_bar_ev'] * flexSpectrum.phys_const['c'])
        
        # Frequency square:
        w2 = _w2_space_(shape, pixelsize)
        
        return numpy.exp(1j * w2 * r_eff / (2*k))
       
def _w_space_(shape, dim, pixelsize):
    """
    Generate spatial frequencies along dimension dim.
    """                   
    # Image dimentions:
    sz = numpy.array(shape) * pixelsize
        
    # Frequency:
    xx = numpy.arange(0, shape[dim]) - shape[dim]//2
    return 2 * numpy.pi * xx / sz[dim]

def _w2_space_(shape, pixelsize):
    """
    Generates the lambda*freq**2*R image that can be used to calculate phase propagator at distance R, photon wavelength lambda.
    """
    # Frequency squared:
    u = _w_space_(shape, 0, pixelsize)
    v = _w_space_(shape, 1, pixelsize)
    return numpy.fft.fftshift((u**2)[:, None] + (v**2)[None, :])
        
def apply_ctf(image, ctf):
    """
    Apply CTF to the image using convolution.
    """
    if image.ndim > 2:
        return numpy.fft.ifft2( numpy.fft.fft2(image, axes = (0, 2)) * ctf , axes = (0, 2))
    
    else:        
        return numpy.fft.ifft2( numpy.fft.fft2(image) * ctf )
      
def apply_phase_contrast():
    pass

def apply_noise(image, mode = 'poisson', parameter = 1):
    """
    Add noise to the data.
    
    Args:
        image (numpy.array): image to apply noise to
        mode (str): poisson or normal
        parameter (float): norm factor for poisson or a standard deviation    
    """
    
    if mode == 'poisson':
        image = numpy.random.poisson(image * parameter)
        
    elif mode == 'normal':
        image = numpy.random.normal(image, parameter)
        
    else: 
        raise ValueError('Me not recognize the mode! Use normal or poisson!')
