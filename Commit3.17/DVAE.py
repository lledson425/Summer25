#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from IPython import display
import matplotlib.pyplot as plt
import numpy as np
import tensorflow as tf
import keras
import tensorflow_probability as tfp
import time
import argparse 
import math

class VAE:
    def __init__(
        self,
        train_images=np.array([]),
        test_images=np.array([]),
        batch_size=32,
        epochs=50,
        latent_dim=2,
        patience=0,
        base_epochs=200,
        learning_rate=1e-4,
        load=''
    ):
        self.epochs = epochs
        self.latent_dim = latent_dim
        self.batch_size = batch_size
        self.patience = patience
        self.base_epochs = base_epochs
        self.optimizer = tf.keras.optimizers.Adam(learning_rate)
        self.load = load
        if self.load == '':
            self.train_images = self.preprocess_images(train_images)
            self.test_images = self.preprocess_images(test_images)
            self.image_dim = self.train_images[0].shape[0]
            self.train_batch, self.test_batch = self.batch_images(self.train_images, self.test_images, self.batch_size)
            self.model = self.CVAE(self.latent_dim, self.image_dim)
            self.losses, self.train_losses = self.train_model(self.model, self.epochs, self.train_batch, self.test_batch, self.optimizer, self.patience, self.base_epochs)
        else:
            self.model = tf.keras.models.load_model(self.load, custom_objects={'CVAE': self.CVAE})
            self.losses, self.train_losses = (np.array([]), np.array([]))

    def preprocess_images(self, images) -> np.array:
        images = images.reshape(images.shape[0], images.shape[1]*images.shape[2]) / np.max(images, axis=(1,2)).reshape(-1,1)
        images = images.reshape((images.shape[0], int(images.shape[1]**0.5), int(images.shape[1]**0.5), 1))
        images = (images + 1) / 2.0
        return np.array(images).astype('float32')

    def batch_images(self, train_images, test_images, batch_size):
        train_size = train_images.shape[0]
        test_size = test_images.shape[0]
        train_batch = tf.data.Dataset.from_tensor_slices(train_images).shuffle(train_size).batch(batch_size)
        test_batch = tf.data.Dataset.from_tensor_slices(test_images).shuffle(test_size).batch(batch_size)
        return train_batch, test_batch

    @staticmethod
    def compute_conv2d_layers(image_dim, base_filters=32, target_dim=8):
        if image_dim < target_dim:
            raise ValueError(f"image_dim ({image_dim}) must be >= target_dim ({target_dim})")
        layers = []
        num_layers = int(round(math.log(image_dim / target_dim, 2)))
        for i in range(num_layers):
            filters = base_filters * (2 ** i)
            layers.append(tf.keras.layers.Conv2D(filters, 4, strides=2, padding='same', activation='relu'))
        return layers, num_layers

    @staticmethod
    def compute_deconv2d_layers(image_dim, base_filters=32, target_dim=8):
        if image_dim < target_dim:
            raise ValueError(f"image_dim ({image_dim}) must be >= target_dim ({target_dim})")
        num_layers = int(round(math.log(image_dim / target_dim, 2)))
        layers = []
        for i in reversed(range(num_layers)):
            filters = base_filters * (2 ** i)
            layers.append(tf.keras.layers.Conv2DTranspose(filters, 4, strides=2, padding='same', activation='relu'))
        return layers, num_layers

    @keras.saving.register_keras_serializable()
    class CVAE(tf.keras.Model):
        def __init__(self, latent_dim, image_dim, **kwargs):
            super(VAE.CVAE, self).__init__(**kwargs)
            self.latent_dim = latent_dim
            self.image_dim = image_dim
            base_filters = 48
            target_dim = 4

            # Encoder
            conv_layers, num_layers = VAE.compute_conv2d_layers(image_dim, base_filters, target_dim)
            self.encoder = tf.keras.Sequential(
                [tf.keras.layers.InputLayer(input_shape=(image_dim, image_dim, 1))] +
                conv_layers +
                [tf.keras.layers.Flatten(),
                 tf.keras.layers.Dense(latent_dim * 2)]
            )

            # Decoder
            dense_units = (target_dim ** 2) * (base_filters * (2 ** (num_layers - 1)))
            deconv_layers = VAE.compute_deconv2d_layers(image_dim, base_filters, target_dim)[0]
            self.decoder = tf.keras.Sequential(
                [tf.keras.layers.InputLayer(input_shape=(latent_dim,)),
                 tf.keras.layers.Dense(units=dense_units, activation='relu'),
                 tf.keras.layers.Reshape((target_dim, target_dim, base_filters * (2 ** (num_layers - 1))))] +
                deconv_layers +
                [tf.keras.layers.Conv2DTranspose(1, 4, strides=1, padding='same')]
            )

        def sample(self, eps=None):
            if eps is None:
                eps = tf.random.normal(shape=(100, self.latent_dim))
            return self.decode(eps, apply_sigmoid=True)

        def encode(self, x):
            mean, logvar = tf.split(self.encoder(x), num_or_size_splits=2, axis=1)
            return mean, logvar

        def reparameterize(self, mean, logvar):
            eps = tf.random.normal(shape=mean.shape)
            return eps * tf.exp(logvar * .5) + mean

        def decode(self, z, apply_sigmoid=False):
            logits = self.decoder(z)
            return tf.sigmoid(logits) if apply_sigmoid else logits

        def get_config(self):
            config = super().get_config()
            config.update({
                'latent_dim': self.latent_dim,
                'image_dim': self.image_dim,
            })
            return config

    def log_normal_pdf(self, sample, mean, logvar, raxis=1):
        log2pi = tf.math.log(2. * np.pi)
        return tf.reduce_sum(-.5 * ((sample - mean)**2. * tf.exp(-logvar) + logvar + log2pi), axis=raxis)

    def compute_loss(self, model, x):
        mean, logvar = model.encode(x)
        z = model.reparameterize(mean, logvar)
        x_logit = model.decode(z)
        cross_ent = tf.nn.sigmoid_cross_entropy_with_logits(logits=x_logit, labels=x)
        logpx_z = -tf.reduce_sum(cross_ent, axis=[1, 2, 3])
        logpz = self.log_normal_pdf(z, 0., 0.)
        logqz_x = self.log_normal_pdf(z, mean, logvar)
        return -tf.reduce_mean(logpx_z + logpz - logqz_x)

    @tf.function
    def train_step(self, model, x, optimizer):
        with tf.GradientTape() as tape:
            loss = self.compute_loss(model, x)
        gradients = tape.gradient(loss, model.trainable_variables)
        optimizer.apply_gradients(zip(gradients, model.trainable_variables))

    def train_model(self, model, epochs, train_dataset, test_dataset, optimizer, patience, base_epochs):
        losses = []
        train_losses = []
        for epoch in range(1, epochs + 1):
            start_time = time.time()
            for train_x in train_dataset:
                self.train_step(model, train_x, optimizer)
            end_time = time.time()
            loss = tf.keras.metrics.Mean()
            for test_x in test_dataset:
                loss(self.compute_loss(model, test_x))
            elbo = -loss.result()
            losses.append(loss.result())
            train_loss = tf.keras.metrics.Mean()
            for train_x in train_dataset:
                train_loss(self.compute_loss(model, train_x))
            train_losses.append(train_loss.result())

            if patience > 0 and epoch >= patience + base_epochs:
                half = patience // 2
                first = np.array(losses[-patience:-half])
                second = np.array(losses[-half:])
                if abs(np.mean(first) - np.mean(second)) <= (np.std(first)/len(first)**0.5)**2 + (np.std(second)/len(second)**0.5)**2:
                    break
            display.clear_output(wait=False)
            print(f"Epoch: {epoch}, Test set ELBO: {elbo:.4f}, time elapse for current epoch: {end_time - start_time:.2f}s")

        return losses, train_losses

    def plot_loss(self):
        fig = plt.figure(figsize=(6, 5))
        plt.plot(self.losses)
        plt.title("Loss vs Epoch")
        plt.xlabel("Epoch")
        plt.ylabel("Loss")
        plt.show()

    def get_loss(self):
        return self.losses if len(self.losses) > 0 else print("Cannot get loss for loaded model")

    def get_train_loss(self):
        return self.train_losses if len(self.train_losses) > 0 else print("Cannot get loss for loaded model")

    def encode(self, images, mean=True, both=False):
        images = self.preprocess_images(np.array(images))
        return self.model.encode(images) if both else (self.model.encode(images)[0] if mean else self.model.encode(images)[1])

    def decode(self, data, apply_sigmoid=False):
        return self.model.decode(data, apply_sigmoid)

    def reparameterize(self, mean, logvar):
        return self.model.reparameterize(mean, logvar)

    def saveModel(self, filepath):
        self.model.save(filepath)
