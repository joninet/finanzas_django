from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

class MedioPago(models.Model):
    """Modelo para representar los medios de pago disponibles"""
    nombre = models.CharField(_('Nombre'), max_length=100, unique=True)
    activo = models.BooleanField(_('Activo'), default=True)
    
    class Meta:
        verbose_name = _('Medio de Pago')
        verbose_name_plural = _('Medios de Pago')
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre


class Categoria(models.Model):
    """Modelo para categorías de gastos e ingresos"""
    TIPO_CHOICES = (
        ('gasto', 'Gasto'),
        ('ingreso', 'Ingreso'),
    )
    
    nombre = models.CharField(_('Nombre'), max_length=100)
    tipo = models.CharField(_('Tipo'), max_length=10, choices=TIPO_CHOICES)
    color = models.CharField(_('Color'), max_length=7, help_text='Código de color hexadecimal', blank=True, null=True)
    icon = models.CharField(_('Icono'), max_length=30, blank=True, null=True)
    activo = models.BooleanField(_('Activa'), default=True)
    
    class Meta:
        verbose_name = _('Categoría')
        verbose_name_plural = _('Categorías')
        ordering = ['tipo', 'nombre']
        unique_together = ['nombre', 'tipo']
    
    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_display()})"


class Movimiento(models.Model):
    """Modelo base para gastos e ingresos"""
    TIPO_CHOICES = (
        ('gasto', 'Gasto'),
        ('ingreso', 'Ingreso'),
    )
    
    CATEGORIA_CHOICES = (
        ('fijo', 'Fijo'),
        ('variable', 'Variable'),
    )
    
    ESTADO_CHOICES = (
        ('pendiente', 'Pendiente'),
        ('cancelado', 'Cancelado'),
        ('pagado', 'Pagado'),
    )
    
    concepto = models.CharField(_('Concepto'), max_length=200)
    monto = models.DecimalField(_('Monto'), max_digits=10, decimal_places=2)
    fecha = models.DateField(_('Fecha'))
    tipo = models.CharField(_('Tipo'), max_length=10, choices=TIPO_CHOICES)
    categoria = models.CharField(_('Categoría'), max_length=10, choices=CATEGORIA_CHOICES)
    estado = models.CharField(_('Estado'), max_length=10, choices=ESTADO_CHOICES, default='pendiente')
    medio_pago = models.ForeignKey(MedioPago, on_delete=models.PROTECT, verbose_name=_('Medio de Pago'), related_name='movimientos')
    observaciones = models.TextField(_('Observaciones'), blank=True, null=True)
    fecha_creacion = models.DateTimeField(_('Fecha Creación'), auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(_('Fecha Actualización'), auto_now=True)
    
    class Meta:
        verbose_name = _('Movimiento')
        verbose_name_plural = _('Movimientos')
        ordering = ['-fecha', '-fecha_creacion']
    
    def __str__(self):
        return f"{self.concepto} - {self.monto}"


class Gasto(Movimiento):
    """Modelo para representar gastos"""
    
    def save(self, *args, **kwargs):
        self.tipo = 'gasto'
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = _('Gasto')
        verbose_name_plural = _('Gastos')
        proxy = True


class Ingreso(Movimiento):
    """Modelo para representar ingresos"""
    
    def save(self, *args, **kwargs):
        self.tipo = 'ingreso'
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = _('Ingreso')
        verbose_name_plural = _('Ingresos')
        proxy = True


class Configuracion(models.Model):
    """Modelo para almacenar configuraciones generales"""
    clave = models.CharField(_('Clave'), max_length=100, unique=True)
    valor = models.TextField(_('Valor'))
    descripcion = models.TextField(_('Descripción'), blank=True, null=True)
    
    class Meta:
        verbose_name = _('Configuración')
        verbose_name_plural = _('Configuraciones')
        ordering = ['clave']
    
    def __str__(self):
        return self.clave
